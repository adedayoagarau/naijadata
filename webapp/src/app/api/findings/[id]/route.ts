import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface Finding {
  id?: string;
  type?: string;
  entity?: string;
  description?: string;
  amount?: number;
  severity?: string;
  year?: number;
  state?: string;
  recommendation?: string;
  risk_score?: number;
  risk_factors?: string[];
}

// Load findings from files
function loadFindings(): Finding[] {
  const paths = [
    path.join(process.cwd(), "..", "findings", "webapp_findings.json"),
    path.join(process.cwd(), "data", "findings.json"),
  ];

  for (const p of paths) {
    try {
      if (fs.existsSync(p)) {
        const data = JSON.parse(fs.readFileSync(p, "utf-8"));
        return data.findings || data.items || data;
      }
    } catch (e) {
      console.error(`Failed to load ${p}:`, e);
    }
  }

  // Return demo data if no files found
  return DEMO_FINDINGS;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const findings = loadFindings();

  // Find by ID or index
  let finding = findings.find((f) => f.id === id);

  // If not found by id, try treating id as an index
  if (!finding && !isNaN(Number(id))) {
    finding = findings[Number(id)];
  }

  if (!finding) {
    return NextResponse.json({ error: "Finding not found" }, { status: 404 });
  }

  // Ensure the finding has an id
  if (!finding.id) {
    finding.id = id;
  }

  return NextResponse.json({ finding });
}

// Demo findings for when no data files exist
const DEMO_FINDINGS: Finding[] = [
  {
    id: "1",
    type: "MANDATE_VIOLATION",
    entity: "National Intelligence Agency",
    description:
      "Security agency allocated ₦31.1B for hospital construction - 46x more than the Health Ministry spends on hospital repairs. This represents a severe mandate violation.",
    amount: 31_104_141_419,
    severity: "CRITICAL",
    year: 2026,
    recommendation:
      "Investigate why a spy agency needs to build hospitals. This allocation should be under the Ministry of Health.",
    risk_score: 95,
    risk_factors: [
      "MANDATE_VIOLATION",
      "ROUND_NUMBER",
      "CROSS_MDA_OUTLIER",
      "HIGH_RISK_MDA",
    ],
  },
  {
    id: "2",
    type: "YOY_VARIANCE",
    entity: "National Assembly",
    description:
      "320% increase in travel allowances compared to 2025. Total travel budget now at ₦22.49B for 469 legislators.",
    amount: 22_490_000_000,
    severity: "HIGH",
    year: 2026,
    recommendation:
      "Request itemized breakdown of travel destinations and justification for the increase.",
    risk_score: 85,
    risk_factors: ["YOY_VARIANCE", "HIGH_AMOUNT", "ROUND_NUMBER"],
  },
  {
    id: "3",
    type: "ROUND_NUMBER",
    entity: "Ministry of Works",
    description:
      "Exact ₦10B allocation suggests estimation rather than actual project costing.",
    amount: 10_000_000_000,
    severity: "MEDIUM",
    year: 2026,
    recommendation: "Request detailed project breakdown with cost estimates.",
    risk_score: 60,
    risk_factors: ["ROUND_NUMBER", "VAGUE_DESCRIPTION"],
  },
  {
    id: "4",
    type: "CROSS_MDA_OUTLIER",
    entity: "Office of the NSA",
    description:
      "Spending 8.5x median for budget code 2305 (Security Equipment) compared to peer agencies.",
    amount: 45_000_000_000,
    severity: "CRITICAL",
    year: 2026,
    recommendation:
      "Compare with previous years and similar agencies. Request procurement documentation.",
    risk_score: 92,
    risk_factors: ["CROSS_MDA_OUTLIER", "HIGH_AMOUNT", "HIGH_RISK_MDA"],
  },
];
