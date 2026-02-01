"use client";

import Link from "next/link";

interface Finding {
  id: string;
  type: string;
  entity: string;
  amount: number;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  year: number;
}

interface TopFindingsProps {
  findings: Finding[];
  limit?: number;
  title?: string;
}

const formatAmount = (amount: number): string => {
  if (amount >= 1_000_000_000_000) {
    return `₦${(amount / 1_000_000_000_000).toFixed(1)}T`;
  } else if (amount >= 1_000_000_000) {
    return `₦${(amount / 1_000_000_000).toFixed(1)}B`;
  } else if (amount >= 1_000_000) {
    return `₦${(amount / 1_000_000).toFixed(1)}M`;
  }
  return `₦${amount.toLocaleString()}`;
};

const severityColors = {
  CRITICAL: "#D6453A",
  HIGH: "#164678",
  MEDIUM: "#EBC346",
  LOW: "#D9D9CD",
};

export default function TopFindings({ findings, limit = 5, title = "TOP FINDINGS" }: TopFindingsProps) {
  const topFindings = [...findings]
    .sort((a, b) => (b.amount || 0) - (a.amount || 0))
    .slice(0, limit);

  if (topFindings.length === 0) {
    return null;
  }

  const maxAmount = topFindings[0]?.amount || 1;

  return (
    <div className="bg-[#111] border border-c-border p-4">
      <div className="text-xs text-gray-500 font-mono mb-3">{title}</div>
      <div className="space-y-3">
        {topFindings.map((finding, idx) => (
          <Link
            key={finding.id}
            href={`/finding/${finding.id}`}
            className="block group"
          >
            <div className="flex items-start gap-3">
              <div
                className="w-6 h-6 flex items-center justify-center text-xs font-mono flex-shrink-0"
                style={{ backgroundColor: severityColors[finding.severity], color: finding.severity === "MEDIUM" ? "#000" : "#fff" }}
              >
                {idx + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white text-sm group-hover:text-[#EBC346] transition-colors truncate">
                  {finding.entity}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1.5 bg-[#0a0a0a] rounded overflow-hidden">
                    <div
                      className="h-full"
                      style={{
                        width: `${(finding.amount / maxAmount) * 100}%`,
                        backgroundColor: severityColors[finding.severity],
                      }}
                    />
                  </div>
                  <div className="text-xs text-gray-400 font-mono">
                    {formatAmount(finding.amount)}
                  </div>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <Link
        href="/red-flags"
        className="block mt-4 pt-3 border-t border-[#222] text-xs text-center text-gray-500 hover:text-white transition-colors"
      >
        VIEW ALL RED FLAGS →
      </Link>
    </div>
  );
}
