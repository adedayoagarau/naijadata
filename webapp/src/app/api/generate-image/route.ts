import { NextRequest, NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

// Initialize Gemini
const genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_API_KEY || "");

export async function POST(request: NextRequest) {
  try {
    const { prompt, finding, style = "infographic" } = await request.json();

    if (!process.env.GOOGLE_AI_API_KEY) {
      return NextResponse.json(
        { error: "GOOGLE_AI_API_KEY not configured" },
        { status: 500 }
      );
    }

    // Build the image prompt based on the finding data
    let imagePrompt = prompt;

    if (!imagePrompt && finding) {
      // Generate a prompt based on the finding
      const styleGuides: Record<string, string> = {
        infographic:
          "Clean, professional infographic style with bold typography, data visualization elements, Nigerian green and white color accents",
        editorial:
          "Editorial illustration style, thought-provoking, symbolic representation of government spending and accountability",
        abstract:
          "Abstract geometric art representing financial data, using shapes and colors to convey the magnitude of the amounts",
        photorealistic:
          "Photorealistic depiction of Nigerian government buildings, money, or related imagery that represents budget allocation",
      };

      imagePrompt = `Create a compelling visual for a Nigerian budget transparency report.

Subject: ${finding.entity || "Government Budget"}
Amount: ${finding.amount ? `₦${(finding.amount / 1_000_000_000).toFixed(1)} billion` : "Large allocation"}
Issue: ${finding.description || "Budget anomaly detected"}
Severity: ${finding.severity || "HIGH"}

Style: ${styleGuides[style] || styleGuides.infographic}

The image should be suitable for social media sharing and convey a sense of civic accountability. Include subtle Nigerian visual elements. Do not include any text in the image.`;
    }

    // Use Gemini Pro Vision or Imagen model for image generation
    // Note: As of the SDK version, we might need to use a specific model
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" });

    // For now, generate a descriptive response that could guide image creation
    // Full image generation requires the Imagen API or Gemini with image output
    const result = await model.generateContent([
      {
        text: `You are helping create visual content for Decide9ja, a Nigerian budget transparency platform.

Given this image concept, describe in detail what the image should look like, including composition, colors, and visual elements. This will be used to generate an image.

Concept: ${imagePrompt}

Provide a detailed visual description in JSON format:
{
  "title": "Short title for the image",
  "description": "Detailed description of the visual",
  "colors": ["primary color", "secondary color", "accent color"],
  "elements": ["element 1", "element 2"],
  "mood": "The overall mood/tone",
  "composition": "How elements are arranged"
}`,
      },
    ]);

    const response = result.response;
    const text = response.text();

    // Try to parse as JSON
    let imageSpec;
    try {
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        imageSpec = JSON.parse(jsonMatch[0]);
      }
    } catch {
      imageSpec = { description: text };
    }

    return NextResponse.json({
      success: true,
      imageSpec,
      prompt: imagePrompt,
      note: "Image specification generated. For actual image generation, use Gemini Imagen API or integrate with an image generation service.",
    });
  } catch (error) {
    console.error("Gemini API error:", error);
    return NextResponse.json(
      {
        error: "Failed to generate image specification",
        details: String(error),
      },
      { status: 500 }
    );
  }
}
