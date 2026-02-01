"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface YoYChange {
  mda: string;
  amount_2025: number;
  amount_2026: number;
  change_amount: number;
  change_percentage: number;
}

interface Finding {
  id: string;
  entity: string;
  amount: number;
  severity: string;
  year: number;
  type: string;
  state?: string;
  change_percentage?: number;
  amount_2025?: number;
}

const formatAmount = (amount: number): string => {
  if (amount >= 1_000_000_000_000) {
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`;
  } else if (amount >= 1_000_000_000) {
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`;
  } else if (amount >= 1_000_000) {
    return `₦${(amount / 1_000_000).toFixed(2)}M`;
  }
  return `₦${amount.toLocaleString()}`;
};

// Impact calculator
const IMPACT_BENCHMARKS = {
  primary_school: { cost: 150_000_000, label: "Primary Schools" },
  health_center: { cost: 150_000_000, label: "Health Centers" },
  borehole: { cost: 5_000_000, label: "Boreholes" },
  ambulance: { cost: 50_000_000, label: "Ambulances" },
  yearly_wage: { cost: 840_000, label: "Years of Min. Wage" },
};

function calculateImpact(amount: number): { key: string; count: number; label: string }[] {
  return Object.entries(IMPACT_BENCHMARKS)
    .map(([key, { cost, label }]) => ({
      key,
      count: Math.floor(amount / cost),
      label,
    }))
    .filter((item) => item.count > 0)
    .sort((a, b) => b.count - a.count);
}

export default function ComparePage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<"percentage" | "amount">("percentage");
  const [showIncreases, setShowIncreases] = useState(true);
  const [stateFilter, setStateFilter] = useState<string>("ALL");

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await fetch("/api/findings");
        if (res.ok) {
          const data = await res.json();
          setFindings(data.findings || []);
        }
      } catch (err) {
        console.error("Failed to load findings:", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  // Get unique states for filter
  const states = [...new Set(findings.map((f) => f.state).filter(Boolean))].sort() as string[];

  // Only show findings with ACTUAL YoY comparison data
  const yoyFindings = findings
    .filter(
      (f) =>
        // Must have actual comparison data - either change_percentage or amount_2025
        (f.change_percentage !== undefined && f.change_percentage !== null) ||
        (f.amount_2025 !== undefined && f.amount_2025 > 0) ||
        f.type === "YOY_VARIANCE" ||
        f.type === "YOY_SPIKE"
    )
    .filter((f) => {
      if (stateFilter === "ALL") return true;
      if (stateFilter === "FEDERAL") return !f.state;
      return f.state === stateFilter;
    })
    .map((f) => {
      // Calculate change percentage from actual data
      let calculatedChange = f.change_percentage;
      if ((calculatedChange === undefined || calculatedChange === null) && f.amount_2025 && f.amount_2025 > 0) {
        // Real calculation: (new - old) / old * 100
        calculatedChange = ((f.amount - f.amount_2025) / f.amount_2025) * 100;
      }

      return {
        ...f,
        entity: f.entity || f.type?.replace(/_/g, " ") || "Budget Item",
        change_percentage: calculatedChange || 0,
        // Keep the actual amount_2025 - don't fabricate it
        amount_2025: f.amount_2025,
      };
    });

  // Sort
  const sortedFindings = [...yoyFindings].sort((a, b) => {
    if (sortBy === "percentage") {
      return Math.abs(b.change_percentage || 0) - Math.abs(a.change_percentage || 0);
    }
    return b.amount - a.amount;
  });

  // Filter by direction - if no change data, show in increases by default
  const displayFindings = showIncreases
    ? sortedFindings.filter((f) => (f.change_percentage || 0) >= 0)
    : sortedFindings.filter((f) => (f.change_percentage || 0) < 0);

  const today = new Date();
  const dateStr = `${String(today.getMonth() + 1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")}.${String(today.getFullYear()).slice(-2)}`;

  // Calculate totals for increases - only from actual data
  const totalIncrease = sortedFindings
    .filter((f) => (f.change_percentage || 0) > 0 && f.amount_2025 && f.amount_2025 > 0)
    .reduce((sum, f) => sum + (f.amount - f.amount_2025!), 0);

  return (
    <div
      className="min-h-screen bg-c-black pb-20 md:pb-0"
      style={{
        "--c-red": "#D6453A",
        "--c-blue": "#164678",
        "--c-green": "#487A3A",
        "--c-yellow": "#EBC346",
        "--c-beige": "#D9D9CD",
        "--c-brown": "#9E7D45",
        "--c-black": "#050505",
        "--c-border": "#111111",
      } as React.CSSProperties}
    >
      {/* Header */}
      <header className="bg-c-black text-gray-500 px-4 md:px-8 py-4 md:py-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-2 font-display text-xs tracking-wide border-b border-c-border">
        <Link
          href="/"
          className="text-white font-normal text-xs tracking-[0.2em] uppercase hover:text-gray-300 transition-colors"
        >
          Decide9ja // Budget Transparency DB
        </Link>
        <nav className="flex gap-4 md:gap-16 text-[10px] md:text-xs">
          <Link href="/red-flags" className="text-gray-500 hover:text-white transition-colors">
            RED FLAGS
          </Link>
          <Link href="/explore" className="text-gray-500 hover:text-white transition-colors">
            EXPLORE
          </Link>
          <Link href="/compare" className="text-white transition-colors">
            COMPARE
          </Link>
          <Link href="/about" className="text-gray-500 hover:text-white transition-colors">
            ABOUT
          </Link>
          <span className="text-gray-600">{dateStr}</span>
        </nav>
      </header>

      {/* Page Title */}
      <div className="bg-[#EBC346] px-4 md:px-8 py-6">
        <h1 className="text-2xl md:text-4xl font-bold text-black">YEAR-OVER-YEAR COMPARISON</h1>
        <p className="text-black/70 mt-1">2025 vs 2026 Budget Changes</p>
      </div>

      {/* Summary Stats */}
      <div className="bg-[#111] border-b border-c-border px-4 md:px-8 py-4">
        <div className="flex flex-wrap gap-6 text-sm font-mono">
          <div>
            <span className="text-gray-500">TOTAL INCREASES:</span>{" "}
            <span className="text-[#D6453A] font-bold">{formatAmount(totalIncrease)}</span>
          </div>
          <div>
            <span className="text-gray-500">MDAs WITH SPIKES:</span>{" "}
            <span className="text-white">{yoyFindings.filter((f) => (f.change_percentage || 0) > 100).length}</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-c-black border-b border-c-border px-4 md:px-8 py-4 flex flex-wrap gap-3 items-center">
        <div className="flex border border-gray-600 rounded overflow-hidden">
          <button
            onClick={() => setShowIncreases(true)}
            className={`px-4 py-2 text-xs ${showIncreases ? "bg-[#D6453A] text-white" : "text-gray-400 hover:text-white"}`}
          >
            Increases ↑
          </button>
          <button
            onClick={() => setShowIncreases(false)}
            className={`px-4 py-2 text-xs ${!showIncreases ? "bg-[#487A3A] text-white" : "text-gray-400 hover:text-white"}`}
          >
            Decreases ↓
          </button>
        </div>

        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          className="bg-transparent border border-gray-600 text-white text-xs px-3 py-2 rounded"
        >
          <option value="ALL">All Jurisdictions</option>
          <option value="FEDERAL">Federal</option>
          {states.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "percentage" | "amount")}
          className="bg-transparent border border-gray-600 text-white text-xs px-3 py-2 rounded"
        >
          <option value="percentage">Sort by % Change</option>
          <option value="amount">Sort by Amount</option>
        </select>

        <span className="text-gray-500 text-xs ml-auto">{displayFindings.length} results</span>
      </div>

      {/* Content */}
      <div className="px-4 md:px-8 py-6">
        {loading ? (
          <div className="text-center text-gray-500 py-12">Loading comparison data...</div>
        ) : displayFindings.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <p className="text-lg">No year-over-year changes found</p>
            <p className="text-sm mt-2">Run the outrage generator to detect YoY spikes</p>
          </div>
        ) : (
          <div className="space-y-4">
            {displayFindings.map((finding) => {
              // Only calculate change if we have actual 2025 data
              const has2025Data = finding.amount_2025 && finding.amount_2025 > 0;
              const changeAmt = has2025Data ? finding.amount - finding.amount_2025 : 0;
              const impact = calculateImpact(Math.abs(has2025Data ? changeAmt : finding.amount));
              const isIncrease = (finding.change_percentage || 0) > 0;

              return (
                <div
                  key={finding.id}
                  className={`bg-[#111] border-l-4 ${isIncrease ? "border-l-[#D6453A]" : "border-l-[#487A3A]"} p-4 md:p-6`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                    {/* Left: Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className={`px-2 py-1 text-xs font-mono ${isIncrease ? "bg-[#D6453A] text-white" : "bg-[#487A3A] text-white"}`}
                        >
                          {isIncrease ? "↑" : "↓"} {Math.abs(finding.change_percentage || 0).toFixed(0)}%
                        </span>
                        <span className="text-gray-500 text-xs">{finding.type?.replace(/_/g, " ")}</span>
                      </div>

                      <h3 className="text-white text-lg md:text-xl font-medium mb-2">{finding.entity}</h3>

                      {/* Year comparison - only show if we have actual data */}
                      {has2025Data ? (
                        <div className="flex items-center gap-4 text-sm mb-3">
                          <div>
                            <span className="text-gray-500">2025:</span>{" "}
                            <span className="text-white">{formatAmount(finding.amount_2025!)}</span>
                          </div>
                          <span className="text-gray-600">→</span>
                          <div>
                            <span className="text-gray-500">2026:</span>{" "}
                            <span className="text-white font-bold">{formatAmount(finding.amount)}</span>
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm mb-3">
                          <span className="text-gray-500">2026 Amount:</span>{" "}
                          <span className="text-white font-bold">{formatAmount(finding.amount)}</span>
                        </div>
                      )}

                      {/* Change amount - only show if we have actual comparison */}
                      {has2025Data && (
                        <div className={`text-lg font-bold ${isIncrease ? "text-[#D6453A]" : "text-[#487A3A]"}`}>
                          {isIncrease ? "+" : ""}
                          {formatAmount(changeAmt)}
                        </div>
                      )}
                    </div>

                    {/* Right: Impact */}
                    <div className="lg:w-64 bg-[#0a0a0a] p-4 rounded">
                      <div className="text-xs text-gray-500 mb-2 font-mono">
                        {has2025Data ? "WHAT THE CHANGE COULD BUILD:" : "WHAT THIS COULD BUILD:"}
                      </div>
                      <div className="space-y-1">
                        {impact.slice(0, 3).map((item) => (
                          <div key={item.key} className="flex justify-between text-sm">
                            <span className="text-gray-400">{item.label}</span>
                            <span className="text-[#EBC346] font-mono">{item.count.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Share buttons */}
                  <div className="mt-4 pt-4 border-t border-[#222] flex gap-2">
                    <button
                      onClick={() => {
                        const text = has2025Data
                          ? `🚨 ${finding.entity}: ${Math.abs(finding.change_percentage || 0).toFixed(0)}% ${isIncrease ? "INCREASE" : "decrease"}!\n\n2025: ${formatAmount(finding.amount_2025!)}\n2026: ${formatAmount(finding.amount)}\n\nChange: ${isIncrease ? "+" : ""}${formatAmount(changeAmt)}\n\n#Decide9ja #BudgetTransparency`
                          : `🚨 ${finding.entity}: ${formatAmount(finding.amount)} (${Math.abs(finding.change_percentage || 0).toFixed(0)}% YoY)\n\n#Decide9ja #BudgetTransparency`;
                        window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, "_blank");
                      }}
                      className="px-3 py-1 bg-c-black border border-gray-600 text-white text-xs hover:bg-[#111]"
                    >
                      Share on X
                    </button>
                    <button
                      onClick={() => {
                        const text = has2025Data
                          ? `🚨 *BUDGET ALERT*\n\n*${finding.entity}*\n${Math.abs(finding.change_percentage || 0).toFixed(0)}% ${isIncrease ? "INCREASE" : "decrease"}\n\n2025: ${formatAmount(finding.amount_2025!)}\n2026: ${formatAmount(finding.amount)}\n\n_Source: Decide9ja_`
                          : `🚨 *BUDGET ALERT*\n\n*${finding.entity}*\n${formatAmount(finding.amount)} (${Math.abs(finding.change_percentage || 0).toFixed(0)}% YoY)\n\n_Source: Decide9ja_`;
                        window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
                      }}
                      className="px-3 py-1 bg-[#25D366] text-white text-xs hover:brightness-90"
                    >
                      WhatsApp
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Call to Action */}
      <div className="bg-[#111] border-t border-c-border px-4 md:px-8 py-8 text-center">
        <h3 className="text-white text-xl font-bold mb-2">Demand Accountability</h3>
        <p className="text-gray-400 text-sm mb-4">
          Share these findings. Tag your representatives. Make your voice heard.
        </p>
        <div className="flex justify-center gap-3">
          <Link
            href="/red-flags"
            className="px-6 py-3 bg-[#D6453A] text-white font-mono text-sm uppercase hover:brightness-90"
          >
            View All Red Flags
          </Link>
          <Link
            href="/explore"
            className="px-6 py-3 bg-[#164678] text-white font-mono text-sm uppercase hover:brightness-90"
          >
            Explore Budgets
          </Link>
        </div>
      </div>
    </div>
  );
}
