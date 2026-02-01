"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface Finding {
  id: string;
  type: string;
  entity: string;
  description: string;
  amount: number;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  year: number;
  state?: string;
  recommendation?: string;
  risk_score?: number;
  risk_factors?: string[];
}

// Format amount in Naira
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

// Severity colors
const severityColors = {
  CRITICAL: { bg: "bg-[#D6453A]", text: "text-black" },
  HIGH: { bg: "bg-[#164678]", text: "text-white" },
  MEDIUM: { bg: "bg-[#EBC346]", text: "text-black" },
  LOW: { bg: "bg-[#D9D9CD]", text: "text-black" },
};

export default function FindingPage() {
  const params = useParams();
  const router = useRouter();
  const [finding, setFinding] = useState<Finding | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadFinding = async () => {
      try {
        const res = await fetch(`/api/findings/${params.id}`);
        if (res.ok) {
          const data = await res.json();
          setFinding(data.finding);
        } else {
          // Try fetching all findings and filter
          const allRes = await fetch("/api/findings");
          if (allRes.ok) {
            const data = await allRes.json();
            const found = data.findings?.find(
              (f: Finding) => f.id === params.id
            );
            if (found) {
              setFinding(found);
            }
          }
        }
      } catch (err) {
        console.error("Failed to load finding:", err);
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      loadFinding();
    }
  }, [params.id]);

  // Update document title when finding loads
  useEffect(() => {
    if (finding) {
      document.title = `${finding.entity} | Decide9ja`;
    } else if (!loading) {
      document.title = "Finding Not Found | Decide9ja";
    }
  }, [finding, loading]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-white font-mono animate-pulse">
          Loading finding...
        </div>
      </div>
    );
  }

  if (!finding) {
    return (
      <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center gap-4">
        <div className="text-white text-2xl">Finding not found</div>
        <Link href="/" className="text-[#EBC346] hover:underline">
          ← Back to dashboard
        </Link>
      </div>
    );
  }

  const colors = severityColors[finding.severity] || severityColors.MEDIUM;
  const shareUrl =
    typeof window !== "undefined" ? window.location.href : "";
  const shareText = `${finding.entity}: ${formatAmount(finding.amount)}\n\n${finding.description}\n\n#Decide9ja #BudgetTransparency`;
  const tweetUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;

  return (
    <div
      className="min-h-screen bg-[#050505]"
      style={
        {
          "--c-red": "#D6453A",
          "--c-blue": "#164678",
          "--c-green": "#487A3A",
          "--c-yellow": "#EBC346",
          "--c-beige": "#D9D9CD",
          "--c-brown": "#9E7D45",
          "--c-black": "#050505",
        } as React.CSSProperties
      }
    >
      {/* Header */}
      <header className="border-b border-gray-800 px-4 md:px-8 py-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <Link
            href="/"
            className="text-white font-normal text-xs tracking-[0.2em] uppercase hover:text-[#EBC346] transition-colors"
          >
            ← Decide9ja
          </Link>
          <span className="text-gray-500 text-xs font-mono">
            FINDING #{finding.id}
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 md:px-8 py-8 md:py-12">
        {/* Severity Badge */}
        <div className="flex items-center gap-4 mb-6">
          <span
            className={`${colors.bg} ${colors.text} px-4 py-2 text-sm font-bold tracking-wider`}
          >
            {finding.severity}
          </span>
          <span className="text-gray-500 text-sm uppercase tracking-wide">
            {finding.type?.replace(/_/g, " ")}
          </span>
        </div>

        {/* Amount */}
        {finding.amount > 0 && (
          <div className="text-[#D6453A] text-5xl md:text-7xl font-bold mb-4">
            {formatAmount(finding.amount)}
          </div>
        )}

        {/* Entity */}
        <h1 className="text-white text-3xl md:text-4xl font-semibold mb-4 leading-tight">
          {finding.entity}
        </h1>

        {/* Meta info */}
        <div className="flex flex-wrap gap-4 text-gray-500 text-sm mb-8">
          <span>{finding.year} Budget</span>
          {finding.state && <span>• {finding.state}</span>}
          {finding.risk_score && (
            <span>• Risk Score: {finding.risk_score}/100</span>
          )}
        </div>

        {/* Description */}
        <div className="bg-gray-900/50 border border-gray-800 p-6 mb-8">
          <p className="text-gray-300 text-lg leading-relaxed">
            {finding.description}
          </p>
        </div>

        {/* Risk Factors */}
        {finding.risk_factors && finding.risk_factors.length > 0 && (
          <div className="mb-8">
            <h3 className="text-[#EBC346] text-sm font-bold mb-3 tracking-wider">
              RISK FACTORS
            </h3>
            <div className="flex flex-wrap gap-2">
              {finding.risk_factors.map((factor, idx) => (
                <span
                  key={idx}
                  className="bg-gray-800 text-gray-300 px-3 py-1 text-sm"
                >
                  {factor}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Recommendation */}
        {finding.recommendation && (
          <div className="bg-[#EBC346]/10 border-l-4 border-[#EBC346] p-6 mb-8">
            <h3 className="text-[#EBC346] text-sm font-bold mb-2 tracking-wider">
              RECOMMENDATION
            </h3>
            <p className="text-gray-300">{finding.recommendation}</p>
          </div>
        )}

        {/* Share Section */}
        <div className="border-t border-gray-800 pt-8">
          <h3 className="text-white text-sm font-bold mb-4 tracking-wider">
            SHARE THIS FINDING
          </h3>
          <div className="flex flex-wrap gap-4">
            <a
              href={tweetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white text-black px-6 py-3 font-mono text-sm uppercase hover:bg-gray-200 transition-colors"
            >
              Share on X
            </a>
            <button
              onClick={() => {
                navigator.clipboard.writeText(`${shareText}\n\n${shareUrl}`);
                alert("Copied to clipboard!");
              }}
              className="border border-gray-600 text-white px-6 py-3 font-mono text-sm uppercase hover:bg-gray-800 transition-colors"
            >
              Copy Link
            </button>
            <a
              href={`/api/og?entity=${encodeURIComponent(finding.entity)}&amount=${finding.amount}&severity=${finding.severity}&type=${finding.type}&description=${encodeURIComponent(finding.description || "")}&year=${finding.year}`}
              target="_blank"
              rel="noopener noreferrer"
              className="border border-gray-600 text-gray-400 px-6 py-3 font-mono text-sm uppercase hover:bg-gray-800 hover:text-white transition-colors"
            >
              View Card Image
            </a>
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-12 text-center">
          <p className="text-[#EBC346] text-lg mb-4">
            Demand accountability. Share with #Decide9ja
          </p>
          <Link
            href="/"
            className="text-gray-500 hover:text-white transition-colors"
          >
            ← Explore more findings
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 px-4 md:px-8 py-6 mt-12">
        <div className="max-w-4xl mx-auto text-center text-gray-600 text-sm">
          Decide9ja • Budget Transparency for Nigeria
        </div>
      </footer>
    </div>
  );
}
