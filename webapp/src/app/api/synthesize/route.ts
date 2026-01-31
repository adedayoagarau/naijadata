import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";

// Initialize Kimi client (OpenAI-compatible API)
const kimi = process.env.MOONSHOT_API_KEY
  ? new OpenAI({
      apiKey: process.env.MOONSHOT_API_KEY,
      baseURL: "https://api.moonshot.cn/v1",
    })
  : null;

// Initialize Claude client as fallback
const claude = process.env.ANTHROPIC_API_KEY
  ? new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
  : null;

// Load findings for context
function loadFindings() {
  const findingsPath = path.join(
    process.cwd(),
    "..",
    "findings",
    "webapp_findings.json"
  );
  try {
    if (fs.existsSync(findingsPath)) {
      const data = JSON.parse(fs.readFileSync(findingsPath, "utf-8"));
      return data.findings || [];
    }
  } catch (e) {
    console.error("Failed to load findings:", e);
  }
  return [];
}

// Load budget context
function loadBudgetContext() {
  const contextPath = path.join(
    process.cwd(),
    "..",
    "data",
    "context",
    "corruption_patterns.json"
  );
  try {
    if (fs.existsSync(contextPath)) {
      return JSON.parse(fs.readFileSync(contextPath, "utf-8"));
    }
  } catch (e) {
    console.error("Failed to load context:", e);
  }
  return null;
}

const SYSTEM_PROMPT = `You are a Nigerian budget analyst and investigative journalist working for Decide9ja, a civic tech platform promoting budget transparency.

Your role is to synthesize budget data into compelling, accessible narratives that Nigerian citizens can understand and share. You should:

1. Translate complex budget figures into relatable terms (e.g., "This amount could build 200 schools")
2. Identify patterns of potential misuse across MDAs
3. Suggest specific questions citizens should ask their representatives
4. Create shareable summaries suitable for social media
5. Maintain factual accuracy - only state what the data shows

Context about Nigerian budget corruption patterns:
- Budget padding: inflating figures above actual needs
- Ghost projects: projects that exist only on paper
- Mandate violations: agencies spending outside their statutory functions
- Procurement splitting: breaking contracts to avoid oversight thresholds

Always end with actionable recommendations for citizens.
Use Naira (₦) formatting: ₦M for millions, ₦B for billions, ₦T for trillions.`;

export async function POST(request: NextRequest) {
  try {
    const { task, findings, query, format = "report", provider = "auto" } = await request.json();

    if (!kimi && !claude) {
      return NextResponse.json(
        { error: "No API keys configured (MOONSHOT_API_KEY or ANTHROPIC_API_KEY)" },
        { status: 500 }
      );
    }

    // Load context if not provided
    const findingsData = findings || loadFindings();
    const patterns = loadBudgetContext();

    let prompt = "";

    switch (task) {
      case "synthesize_findings":
        prompt = `Analyze these budget findings and create a synthesis report:

${JSON.stringify(findingsData.slice(0, 20), null, 2)}

Create a ${format === "twitter" ? "Twitter thread (max 5 tweets)" : "detailed report"} that:
1. Highlights the most critical issues
2. Shows patterns across different agencies
3. Calculates total amounts at risk
4. Suggests citizen actions

${query ? `Focus on: ${query}` : ""}`;
        break;

      case "generate_narrative":
        prompt = `Create a compelling narrative about this budget finding for Nigerian citizens:

${JSON.stringify(findingsData[0], null, 2)}

Make it:
- Easy to understand (assume no finance background)
- Emotionally resonant but factual
- Include real-world comparisons
- End with a call to action
${format === "twitter" ? "Format as a Twitter thread (280 chars each)" : ""}`;
        break;

      case "compare_mdas":
        prompt = `Compare budget allocations across these agencies and identify disparities:

${JSON.stringify(findingsData, null, 2)}

Highlight:
- Which agency has the most suspicious allocations?
- Are there duplicate projects across MDAs?
- What's the total amount flagged?
- Which patterns repeat across agencies?`;
        break;

      case "citizen_brief":
        prompt = `Create a citizen's brief about the Nigerian budget based on these findings:

${JSON.stringify(findingsData.slice(0, 10), null, 2)}

The brief should:
1. Summarize key issues in plain language
2. Explain why each issue matters
3. List specific questions to ask representatives
4. Provide hashtags for social sharing (#Decide9ja)`;
        break;

      case "custom":
        prompt = query || "Summarize the budget findings";
        if (findingsData.length > 0) {
          prompt += `\n\nFindings data:\n${JSON.stringify(findingsData.slice(0, 15), null, 2)}`;
        }
        break;

      default:
        return NextResponse.json(
          { error: "Invalid task. Use: synthesize_findings, generate_narrative, compare_mdas, citizen_brief, or custom" },
          { status: 400 }
        );
    }

    // Try Kimi first, fall back to Claude
    let response = "";
    let model = "";
    let usage: Record<string, unknown> | undefined;

    const useKimi = provider === "kimi" || (provider === "auto" && kimi);
    const useClaude = provider === "claude" || (provider === "auto" && !kimi);

    if (useKimi && kimi) {
      try {
        const completion = await kimi.chat.completions.create({
          model: "kimi-2.5-latest",
          messages: [
            { role: "system", content: SYSTEM_PROMPT },
            { role: "user", content: prompt },
          ],
          temperature: 0.7,
          max_tokens: 4000,
        });
        response = completion.choices[0]?.message?.content || "";
        model = "kimi-2.5";
        usage = completion.usage as unknown as Record<string, unknown>;
      } catch (kimiError) {
        console.error("Kimi API error, falling back to Claude:", kimiError);
        // Fall through to Claude
      }
    }

    // Use Claude if Kimi failed or wasn't used
    if (!response && claude) {
      const completion = await claude.messages.create({
        model: "claude-sonnet-4-20250514",
        max_tokens: 4000,
        system: SYSTEM_PROMPT,
        messages: [{ role: "user", content: prompt }],
      });
      response =
        completion.content[0].type === "text"
          ? completion.content[0].text
          : "";
      model = "claude-sonnet";
      usage = {
        input_tokens: completion.usage.input_tokens,
        output_tokens: completion.usage.output_tokens,
      };
    }

    if (!response) {
      return NextResponse.json(
        { error: "All synthesis providers failed" },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      task,
      response,
      model,
      usage,
    });
  } catch (error) {
    console.error("Synthesis API error:", error);
    return NextResponse.json(
      {
        error: "Failed to synthesize data",
        details: String(error),
      },
      { status: 500 }
    );
  }
}
