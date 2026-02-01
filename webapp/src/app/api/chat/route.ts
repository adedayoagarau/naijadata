import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// === TOOL IMPLEMENTATIONS ===

interface LineItem {
  code?: string;
  description?: string;
  amount?: number;
  flag?: string;
}

interface MDA {
  code?: string;
  name?: string;
  category?: string;
  total?: number;
  personnel?: number;
  overhead?: number;
  capital?: number;
  line_items?: LineItem[];
}

interface BudgetData {
  source?: string;
  year?: number;
  document_type?: string;
  total_budget?: number;
  recurrent?: number;
  capital?: number;
  currency?: string;
  mdas?: MDA[];
}

interface Finding {
  id?: string;
  type?: string;
  entity?: string;
  description?: string;
  amount?: number;
  severity?: string;
  year?: number;
  state?: string;
}

// Load context files
function loadContext(filename: string): unknown {
  try {
    const contextPath = path.join(process.cwd(), "..", "data", "context", filename);
    if (fs.existsSync(contextPath)) {
      return JSON.parse(fs.readFileSync(contextPath, "utf-8"));
    }
  } catch (e) {
    console.error(`Failed to load ${filename}:`, e);
  }
  return null;
}

// Load budget data from multiple sources
function loadBudgetData(): BudgetData[] {
  const paths = [
    // Primary: master budget data (all years consolidated)
    path.join(process.cwd(), "..", "extracted", "master_budget_data.json"),
    path.join(process.cwd(), "..", "data", "master", "all_items.json"),
    // Fallback: sample data
    path.join(process.cwd(), "..", "extracted", "sample_budget_data.json"),
    // Individual year files
    path.join(process.cwd(), "..", "extracted", "budget_2026.json"),
    path.join(process.cwd(), "..", "extracted", "budget_2025.json"),
    path.join(process.cwd(), "..", "extracted", "budget_2024.json"),
    // Federal data by year
    path.join(process.cwd(), "..", "data", "federal", "2026", "budget_items.json"),
    path.join(process.cwd(), "..", "data", "federal", "2025", "budget_items.json"),
    path.join(process.cwd(), "..", "data", "federal", "2024", "budget_items.json"),
  ];

  const allData: BudgetData[] = [];
  const loadedPaths: string[] = [];

  for (const p of paths) {
    try {
      if (fs.existsSync(p)) {
        const data = JSON.parse(fs.readFileSync(p, "utf-8"));
        if (Array.isArray(data)) {
          allData.push(...data);
        } else if (data.items) {
          allData.push(...data.items);
        } else if (data.mdas) {
          allData.push(data);
        } else {
          allData.push(data);
        }
        loadedPaths.push(p);
        console.log(`Loaded budget data from: ${p}`);
      }
    } catch (e) {
      console.error(`Failed to load ${p}:`, e);
    }
  }

  console.log(`Total budget data sources loaded: ${loadedPaths.length}, items: ${allData.length}`);
  return allData;
}

// Load findings from multiple sources
// CANONICAL PATH - See WORKTREE.md for data structure
function loadFindings(): Finding[] {
  const paths = [
    // PRIMARY: Consolidated findings (single source of truth)
    path.join(process.cwd(), "..", "findings", "consolidated.json"),
    // FALLBACKS (legacy files)
    path.join(process.cwd(), "..", "findings", "webapp_curated_findings.json"),
    path.join(process.cwd(), "..", "findings", "webapp_findings.json"),
    // Local fallback
    path.join(process.cwd(), "data", "findings.json"),
  ];

  for (const p of paths) {
    try {
      if (fs.existsSync(p)) {
        const data = JSON.parse(fs.readFileSync(p, "utf-8"));
        const items = data.findings || data.items || data;
        if (Array.isArray(items) && items.length > 0) {
          console.log(`Loaded ${items.length} findings from: ${p}`);
          return items;
        }
      }
    } catch (e) {
      console.error(`Failed to load ${p}:`, e);
    }
  }

  return [];
}

function formatNaira(amount: number): string {
  if (amount >= 1_000_000_000_000) {
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`;
  } else if (amount >= 1_000_000_000) {
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`;
  } else if (amount >= 1_000_000) {
    return `₦${(amount / 1_000_000).toFixed(2)}M`;
  } else {
    return `₦${amount.toLocaleString()}`;
  }
}

// Tool: Query budget database
function queryBudget(params: {
  year?: number;
  state?: string;
  mda?: string;
  budget_code?: string;
  min_amount?: number;
  max_amount?: number;
  limit?: number;
}): unknown {
  const budgetData = loadBudgetData();
  let results: Array<{
    source: string;
    year: number;
    mda: string;
    item: string;
    amount: number;
    code: string;
  }> = [];

  for (const budget of budgetData) {
    if (params.year && budget.year !== params.year) continue;
    if (params.state && budget.source?.toLowerCase() !== params.state.toLowerCase()) continue;

    for (const mda of budget.mdas || []) {
      if (params.mda && !mda.name?.toLowerCase().includes(params.mda.toLowerCase())) continue;

      for (const item of mda.line_items || []) {
        if (params.budget_code && !item.code?.startsWith(params.budget_code)) continue;
        if (params.min_amount && (item.amount || 0) < params.min_amount) continue;
        if (params.max_amount && (item.amount || 0) > params.max_amount) continue;

        results.push({
          source: budget.source || "unknown",
          year: budget.year || 0,
          mda: mda.name || "unknown",
          item: item.description || "unknown",
          amount: item.amount || 0,
          code: item.code || "",
        });
      }
    }
  }

  const limit = params.limit || 20;
  results = results.slice(0, limit);

  return {
    count: results.length,
    total_amount: formatNaira(results.reduce((sum, r) => sum + r.amount, 0)),
    items: results.map(r => ({ ...r, amount_formatted: formatNaira(r.amount) })),
  };
}

// Tool: Perform calculations
function calculate(params: {
  operation: string;
  values?: number[];
  query?: { year?: number; state?: string; mda?: string; budget_code?: string };
}): unknown {
  let values = params.values || [];

  if (params.query) {
    const queryResult = queryBudget({ ...params.query, limit: 10000 }) as {
      items: Array<{ amount: number }>;
    };
    values = queryResult.items.map((item) => item.amount);
  }

  if (values.length === 0) {
    return { error: "No values to calculate" };
  }

  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / values.length;
  const sorted = [...values].sort((a, b) => a - b);
  const median = values.length % 2 === 0
    ? (sorted[values.length / 2 - 1] + sorted[values.length / 2]) / 2
    : sorted[Math.floor(values.length / 2)];

  switch (params.operation) {
    case "sum": return { result: sum, formatted: formatNaira(sum) };
    case "average":
    case "mean": return { result: mean, formatted: formatNaira(mean) };
    case "median": return { result: median, formatted: formatNaira(median) };
    case "min": return { result: Math.min(...values), formatted: formatNaira(Math.min(...values)) };
    case "max": return { result: Math.max(...values), formatted: formatNaira(Math.max(...values)) };
    case "count": return { result: values.length };
    case "stats": return {
      count: values.length,
      sum: formatNaira(sum),
      mean: formatNaira(mean),
      median: formatNaira(median),
      min: formatNaira(Math.min(...values)),
      max: formatNaira(Math.max(...values)),
    };
    default: return { error: `Unknown operation: ${params.operation}` };
  }
}

// Tool: Get contextual knowledge
function getContext(params: { topic: string }): unknown {
  const topic = params.topic.toLowerCase();

  if (topic.includes("budget") && topic.includes("code")) {
    return loadContext("budget_codes.json");
  } else if (topic.includes("mda") || topic.includes("mandate")) {
    return loadContext("mda_mandates.json");
  } else if (topic.includes("benchmark") || topic.includes("price")) {
    return loadContext("benchmarks.json");
  } else if (topic.includes("population") || topic.includes("state")) {
    return loadContext("population.json");
  } else if (topic.includes("corruption") || topic.includes("pattern") || topic.includes("fraud")) {
    return loadContext("corruption_patterns.json");
  } else {
    return {
      budget_codes: loadContext("budget_codes.json"),
      mda_mandates: loadContext("mda_mandates.json"),
      benchmarks: loadContext("benchmarks.json"),
      population: loadContext("population.json"),
      corruption_patterns: loadContext("corruption_patterns.json"),
    };
  }
}

// Tool: Search findings
function searchFindings(params: {
  query?: string;
  severity?: string;
  type?: string;
  state?: string;
  min_amount?: number;
  limit?: number;
}): unknown {
  let findings = loadFindings();

  if (params.severity) {
    findings = findings.filter(f => f.severity?.toUpperCase() === params.severity?.toUpperCase());
  }
  if (params.type) {
    findings = findings.filter(f => f.type?.toLowerCase().includes(params.type?.toLowerCase() || ""));
  }
  if (params.state) {
    findings = findings.filter(f => f.state?.toLowerCase() === params.state?.toLowerCase());
  }
  if (params.min_amount) {
    findings = findings.filter(f => (f.amount || 0) >= params.min_amount!);
  }
  if (params.query) {
    const q = params.query.toLowerCase();
    findings = findings.filter(f =>
      f.description?.toLowerCase().includes(q) || f.entity?.toLowerCase().includes(q)
    );
  }

  const limit = params.limit || 10;
  return { count: findings.length, findings: findings.slice(0, limit) };
}

// Tool: Generate breakdown
function generateBreakdown(params: { entity: string; year?: number; by?: string }): unknown {
  const budgetData = loadBudgetData();
  const breakdown: Record<string, number> = {};

  for (const budget of budgetData) {
    if (params.year && budget.year !== params.year) continue;

    for (const mda of budget.mdas || []) {
      if (!mda.name?.toLowerCase().includes(params.entity.toLowerCase())) continue;

      if (params.by === "code") {
        for (const item of mda.line_items || []) {
          const codePrefix = (item.code || "").substring(0, 4);
          breakdown[codePrefix] = (breakdown[codePrefix] || 0) + (item.amount || 0);
        }
      } else {
        breakdown["Personnel"] = (breakdown["Personnel"] || 0) + (mda.personnel || 0);
        breakdown["Overhead"] = (breakdown["Overhead"] || 0) + (mda.overhead || 0);
        breakdown["Capital"] = (breakdown["Capital"] || 0) + (mda.capital || 0);
      }
    }
  }

  const total = Object.values(breakdown).reduce((a, b) => a + b, 0);

  return {
    entity: params.entity,
    year: params.year || "all years",
    breakdown: Object.fromEntries(Object.entries(breakdown).map(([k, v]) => [k, formatNaira(v)])),
    total: formatNaira(total),
    percentages: Object.fromEntries(Object.entries(breakdown).map(([k, v]) => [k, `${((v / total) * 100).toFixed(1)}%`])),
  };
}

// Process tool calls
function processToolCall(toolName: string, toolInput: Record<string, unknown>): unknown {
  switch (toolName) {
    case "query_budget": return queryBudget(toolInput as Parameters<typeof queryBudget>[0]);
    case "calculate": return calculate(toolInput as Parameters<typeof calculate>[0]);
    case "get_context": return getContext(toolInput as Parameters<typeof getContext>[0]);
    case "search_findings": return searchFindings(toolInput as Parameters<typeof searchFindings>[0]);
    case "generate_breakdown": return generateBreakdown(toolInput as Parameters<typeof generateBreakdown>[0]);
    default: return { error: `Unknown tool: ${toolName}` };
  }
}

// Tool definitions for Claude
const AGENT_TOOLS: Anthropic.Tool[] = [
  {
    name: "query_budget",
    description: "Query the Nigerian budget database. Filter by year, state, MDA, budget code prefix, or amount range.",
    input_schema: {
      type: "object" as const,
      properties: {
        year: { type: "number", description: "Budget year (e.g., 2024, 2025, 2026)" },
        state: { type: "string", description: "State name (e.g., Lagos, Osun) or 'federal'" },
        mda: { type: "string", description: "Ministry/Department/Agency name or partial match" },
        budget_code: { type: "string", description: "Budget code prefix (e.g., '2205' for consultancy)" },
        min_amount: { type: "number", description: "Minimum amount in Naira" },
        max_amount: { type: "number", description: "Maximum amount in Naira" },
        limit: { type: "number", description: "Maximum results (default 20)" },
      },
    },
  },
  {
    name: "calculate",
    description: "Calculate sum, average, median, min, max, count, or stats on budget data.",
    input_schema: {
      type: "object" as const,
      properties: {
        operation: { type: "string", enum: ["sum", "average", "mean", "median", "min", "max", "count", "stats"] },
        values: { type: "array", items: { type: "number" }, description: "Numbers to calculate on" },
        query: {
          type: "object",
          properties: { year: { type: "number" }, state: { type: "string" }, mda: { type: "string" }, budget_code: { type: "string" } },
          description: "Query to get values from budget data",
        },
      },
      required: ["operation"],
    },
  },
  {
    name: "get_context",
    description: "Get contextual knowledge about budget codes, MDA mandates, benchmarks, population, or corruption patterns.",
    input_schema: {
      type: "object" as const,
      properties: {
        topic: { type: "string", description: "Topic: 'budget codes', 'mda mandates', 'benchmarks', 'population', 'corruption patterns', or 'all'" },
      },
      required: ["topic"],
    },
  },
  {
    name: "search_findings",
    description: "Search analyzed findings/anomalies by severity, type, state, amount, or text.",
    input_schema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Text to search in descriptions" },
        severity: { type: "string", enum: ["CRITICAL", "HIGH", "MEDIUM", "LOW"] },
        type: { type: "string", description: "Finding type (e.g., 'MANDATE_VIOLATION')" },
        state: { type: "string", description: "State name" },
        min_amount: { type: "number", description: "Minimum amount in Naira" },
        limit: { type: "number", description: "Max results (default 10)" },
      },
    },
  },
  {
    name: "generate_breakdown",
    description: "Generate detailed breakdown of budget allocations for an entity.",
    input_schema: {
      type: "object" as const,
      properties: {
        entity: { type: "string", description: "MDA or entity name to analyze" },
        year: { type: "number", description: "Specific year" },
        by: { type: "string", enum: ["category", "code"], description: "Breakdown by category or budget code" },
      },
      required: ["entity"],
    },
  },
];

// Dynamic budget context builder - loads from extracted data
function buildBudgetContext(): string {
  const budgetData = loadBudgetData();
  const findings = loadFindings();
  const benchmarks = loadContext("benchmarks.json") as Record<string, unknown> | null;
  const population = loadContext("population.json") as Record<string, unknown> | null;

  // Build dynamic summary from loaded data
  let dataSummary = "";

  // PRIMARY DATA: 2026 Budget Findings (anomalies detected)
  if (findings.length > 0) {
    const criticalFindings = findings.filter(f => f.severity === "CRITICAL");
    const highFindings = findings.filter(f => f.severity === "HIGH");
    const totalFlagged = findings.reduce((sum, f) => sum + (f.amount || 0), 0);
    const findingYears = [...new Set(findings.map(f => f.year))].sort();
    const states = [...new Set(findings.map(f => f.state).filter(Boolean))];

    dataSummary += `\n=== 2026 FEDERAL BUDGET ANALYSIS (PRIMARY DATA) ===\n`;
    dataSummary += `We have analyzed the 2026 Federal Budget and detected ${findings.length} anomalies.\n`;
    dataSummary += `Years covered: ${findingYears.join(", ")}\n`;
    dataSummary += `Jurisdictions: Federal + ${states.length} states (${states.slice(0,5).join(", ")}${states.length > 5 ? '...' : ''})\n`;
    dataSummary += `Critical findings: ${criticalFindings.length}, High: ${highFindings.length}\n`;
    dataSummary += `Total flagged amount: ${formatNaira(totalFlagged)}\n`;
    dataSummary += `\nIMPORTANT: Use search_findings tool to query 2026 data!\n`;

    dataSummary += `\n## TOP 2026 FINDINGS:\n`;
    findings.slice(0, 12).forEach((f, i) => {
      dataSummary += `${i + 1}. [${f.severity}] ${f.entity}: ${f.description?.substring(0, 80)}... - ${formatNaira(f.amount || 0)}\n`;
    });
  }

  // SECONDARY DATA: Detailed line items (currently only Osun 2025)
  if (budgetData.length > 0) {
    const sources = [...new Set(budgetData.map(b => b.source))];
    const years = [...new Set(budgetData.map(b => b.year))].sort();

    dataSummary += `\n=== DETAILED LINE-ITEM DATA (SECONDARY) ===\n`;
    dataSummary += `Available: ${sources.join(", ")} - Years: ${years.join(", ")}\n`;
    dataSummary += `Use query_budget for detailed line-item queries on these sources.\n`;
    dataSummary += `Note: 2026 Federal data is in findings, not line items yet.\n`;
  }

  return `You are Decide9ja, an AI assistant that helps Nigerians understand government budgets. You analyze federal and state budgets to expose accountability issues.

Your personality: Direct, factual, slightly outraged at waste. You use Nigerian context and relatable comparisons.

${dataSummary}

=== IMPACT CALCULATOR ===
What Nigerian money can build:
- Primary School (6 classrooms, 240 students): ₦150 million
- Health Center (10,000 people): ₦150 million
- Borehole (500 people): ₦5 million
- Ambulance: ₦50 million
- 1km paved road: ₦150 million
- Affordable house: ₦15 million
- Child vaccination (full): ₦15,000
- Malaria treatment: ₦5,000
- Monthly minimum wage: ₦70,000

=== NIGERIAN CONTEXT ===
- Population: ~220 million
- Minimum wage: ₦70,000/month (₦840,000/year)
- Average income: ~₦2-3 million/year
- Poverty rate: ~40%
- Out of school children: 20+ million
- 36 states + FCT

=== RESPONSE GUIDELINES ===
1. Use your tools (query_budget, search_findings, calculate) to get specific data
2. Make comparisons relatable (X = Y years of minimum wage, Z schools, etc.)
3. Express appropriate concern about waste/anomalies
4. Suggest what the money could have built instead
5. Keep responses concise but impactful
6. Use ₦ symbol for Naira
7. If data isn't available, say so and suggest what data would help
8. End significant findings with: "Share this finding with #Decide9ja to demand accountability"
`;
}

// Cache the context (rebuild on first call)
let cachedContext: string | null = null;
function getBudgetContext(): string {
  if (!cachedContext) {
    cachedContext = buildBudgetContext();
  }
  return cachedContext;
}

// Enhanced system prompt for the Budget Analyst Agent
function getAgentSystemPrompt(): string {
  return `You are the Decide9ja Budget Analyst - an expert forensic auditor specializing in Nigerian government budgets. You help citizens understand, analyze, and identify potential issues in federal and state budget allocations.

Your capabilities:
- Query the budget database for specific items, MDAs, years, or states
- Calculate totals, averages, and statistics on budget allocations
- Access contextual knowledge about budget codes, MDA mandates, procurement benchmarks, and corruption patterns
- Search through analyzed findings and anomalies
- Generate detailed breakdowns of how money is allocated

Your personality:
- Direct and factual - you present data without political bias
- Skeptical but fair - you flag concerns but don't make accusations
- Educational - you explain budget concepts to help citizens understand
- Action-oriented - you suggest what questions to ask or investigations to pursue

When analyzing budgets:
- Always show your work with actual numbers
- Compare to benchmarks when available (e.g., UNESCO 15-20% for education)
- Flag round numbers, unusual increases, or mandate violations
- Use Naira formatting (₦M for millions, ₦B for billions, ₦T for trillions)

Remember: In Nigeria's context, ANY budget item could be suspicious. There are no arbitrary thresholds - you score and report on everything, letting citizens decide what deserves scrutiny.

End significant findings with: "Share this finding with #Decide9ja to demand accountability."

${getBudgetContext()}`;
}

export async function POST(request: NextRequest) {
  try {
    const { message, history, useTools = true } = await request.json();

    // Build conversation messages
    const formattedMessages: Anthropic.MessageParam[] = [
      ...history.slice(-8).map((msg: { role: string; content: string }) => ({
        role: msg.role as "user" | "assistant",
        content: msg.content,
      })),
      {
        role: "user" as const,
        content: message,
      },
    ];

    // If tools enabled, use agentic approach
    if (useTools) {
      let response = await anthropic.messages.create({
        model: "claude-3-5-haiku-20241022",
        max_tokens: 2000,
        system: getAgentSystemPrompt(),
        tools: AGENT_TOOLS,
        messages: formattedMessages,
      });

      // Process tool calls in a loop
      let iterations = 0;
      const maxIterations = 5;

      while (response.stop_reason === "tool_use" && iterations < maxIterations) {
        iterations++;

        const toolUseBlocks = response.content.filter(
          (block): block is Anthropic.ToolUseBlock => block.type === "tool_use"
        );

        const toolResults: Anthropic.ToolResultBlockParam[] = toolUseBlocks.map((toolUse) => ({
          type: "tool_result" as const,
          tool_use_id: toolUse.id,
          content: JSON.stringify(processToolCall(toolUse.name, toolUse.input as Record<string, unknown>)),
        }));

        // Continue with tool results
        formattedMessages.push({
          role: "assistant" as const,
          content: response.content,
        });
        formattedMessages.push({
          role: "user" as const,
          content: toolResults,
        });

        response = await anthropic.messages.create({
          model: "claude-3-5-haiku-20241022",
          max_tokens: 2000,
          system: getAgentSystemPrompt(),
          tools: AGENT_TOOLS,
          messages: formattedMessages,
        });
      }

      // Extract final text
      const textBlocks = response.content.filter(
        (block): block is Anthropic.TextBlock => block.type === "text"
      );
      const responseText = textBlocks.map((b) => b.text).join("\n");

      // Extract key data for card generation
      const amountMatch = responseText.match(/₦[\d.,]+\s*(billion|million|trillion|[BMT])/gi);
      const ratioMatch = responseText.match(/(\d+\.?\d*)\s*[xX]\s*(MORE|TIMES|more|times)/i) ||
                         responseText.match(/(\d+\.?\d*)\s*times/i);

      return NextResponse.json({
        response: responseText,
        data: {
          amount: amountMatch ? amountMatch[0].toUpperCase() : undefined,
          comparison: ratioMatch ? `${ratioMatch[1]}X MORE` : undefined,
          canGenerateCard: amountMatch !== null,
        },
        toolsUsed: iterations > 0,
        usage: response.usage,
      });
    } else {
      // Simple RAG mode (no tools)
      const response = await anthropic.messages.create({
        model: "claude-3-5-haiku-20241022",
        max_tokens: 1500,
        system: getBudgetContext(),
        messages: formattedMessages,
      });

      const textContent = response.content.find((c) => c.type === "text");
      const responseText = textContent ? textContent.text : "I could not generate a response.";

      const amountMatch = responseText.match(/₦[\d.,]+\s*(billion|million|trillion)/gi);
      const ratioMatch = responseText.match(/(\d+\.?\d*)\s*[xX]\s*(MORE|TIMES|more|times)/i) ||
                         responseText.match(/(\d+\.?\d*)\s*times/i);

      return NextResponse.json({
        response: responseText,
        data: {
          amount: amountMatch ? amountMatch[0].toUpperCase() : undefined,
          comparison: ratioMatch ? `${ratioMatch[1]}X MORE` : undefined,
          canGenerateCard: amountMatch !== null,
        },
        toolsUsed: false,
      });
    }
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      {
        response: "Sorry, I encountered an error connecting to my brain. Please try again.",
        error: "Failed to process request",
        details: String(error),
      },
      { status: 500 }
    );
  }
}
