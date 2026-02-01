"use client";

import { useState, useEffect } from "react";
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
  risk_factors?: string[];
  risk_score?: number;
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
  CRITICAL: "bg-[#D6453A]",
  HIGH: "bg-[#164678]",
  MEDIUM: "bg-[#EBC346]",
  LOW: "bg-[#D9D9CD]",
};

export default function ExplorePage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  useEffect(() => {
    const loadFindings = async () => {
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
    loadFindings();
  }, []);

  // Group findings by entity (MDA)
  const mdaGroups = findings.reduce((acc, finding) => {
    const entity = finding.entity || "Unknown";
    if (!acc[entity]) {
      acc[entity] = {
        entity,
        findings: [],
        totalAmount: 0,
        maxSeverity: "LOW" as Finding["severity"],
      };
    }
    acc[entity].findings.push(finding);
    acc[entity].totalAmount += finding.amount || 0;

    const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    if (severityOrder[finding.severity] < severityOrder[acc[entity].maxSeverity]) {
      acc[entity].maxSeverity = finding.severity;
    }

    return acc;
  }, {} as Record<string, { entity: string; findings: Finding[]; totalAmount: number; maxSeverity: Finding["severity"] }>);

  const mdaList = Object.values(mdaGroups)
    .filter((mda) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        mda.entity.toLowerCase().includes(q) ||
        mda.findings.some(
          (f) =>
            f.description?.toLowerCase().includes(q) ||
            f.type?.toLowerCase().includes(q)
        )
      );
    })
    .sort((a, b) => b.totalAmount - a.totalAmount);

  const totalAmount = mdaList.reduce((sum, mda) => sum + mda.totalAmount, 0);
  const totalFindings = mdaList.reduce((sum, mda) => sum + mda.findings.length, 0);

  const today = new Date();
  const dateStr = `${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}.${String(today.getFullYear()).slice(-2)}`;

  // Get unique states for the state explorer
  const states = [...new Set(findings.map((f) => f.state).filter(Boolean))].sort() as string[];

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
        <Link href="/" className="text-white font-normal text-xs tracking-[0.2em] uppercase hover:text-gray-300 transition-colors">
          Decide9ja // Budget Transparency DB
        </Link>
        <nav className="flex gap-4 md:gap-16 text-[10px] md:text-xs">
          <Link href="/red-flags" className="text-gray-500 hover:text-white transition-colors">
            RED FLAGS ({findings.length})
          </Link>
          <Link href="/compare" className="text-gray-500 hover:text-white transition-colors">
            COMPARE
          </Link>
          <Link href="/explore" className="text-white transition-colors">
            EXPLORE
          </Link>
          <Link href="/impact" className="text-gray-500 hover:text-white transition-colors">
            IMPACT
          </Link>
          <Link href="/about" className="text-gray-500 hover:text-white transition-colors">
            ABOUT
          </Link>
          <span className="text-gray-600">{dateStr}</span>
        </nav>
      </header>

      {/* Page Title */}
      <div className="bg-[#164678] px-4 md:px-8 py-6">
        <h1 className="text-2xl md:text-4xl font-bold text-white">EXPLORE BUDGETS</h1>
        <p className="text-white/70 mt-1">
          Browse {mdaList.length} MDAs with {formatAmount(totalAmount)} in flagged spending
        </p>
      </div>

      {/* Search & View Toggle */}
      <div className="bg-c-black border-b border-c-border px-4 md:px-8 py-4 flex flex-wrap gap-3 items-center">
        <input
          type="text"
          placeholder="Search MDAs, descriptions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent border border-gray-600 text-white text-sm px-4 py-2 rounded flex-1 min-w-[200px] placeholder:text-gray-500"
        />
        <div className="flex border border-gray-600 rounded overflow-hidden">
          <button
            onClick={() => setViewMode("grid")}
            className={`px-3 py-2 text-xs ${viewMode === "grid" ? "bg-white text-black" : "text-gray-400 hover:text-white"}`}
          >
            Grid
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`px-3 py-2 text-xs ${viewMode === "list" ? "bg-white text-black" : "text-gray-400 hover:text-white"}`}
          >
            List
          </button>
        </div>
      </div>

      {/* States Quick Access */}
      {states.length > 0 && (
        <div className="bg-[#111] border-b border-c-border px-4 md:px-8 py-3">
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
            <span className="text-gray-500 text-xs whitespace-nowrap">STATES:</span>
            {states.map((s) => (
              <Link
                key={s}
                href={`/state/${s.toLowerCase().replace(/\s+/g, "-")}`}
                className="px-3 py-1 bg-[#1a1a1a] text-gray-300 text-xs rounded hover:bg-[#222] whitespace-nowrap transition-colors"
              >
                {s}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="px-4 md:px-8 py-6">
        {loading ? (
          <div className="text-center text-gray-500 py-12">Loading budget data...</div>
        ) : mdaList.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <p className="text-lg">No MDAs match your search</p>
            <p className="text-sm mt-2">Try a different search term</p>
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mdaList.map((mda) => (
              <Link
                key={mda.entity}
                href={`/red-flags?search=${encodeURIComponent(mda.entity)}`}
                className="bg-[#111] p-5 hover:bg-[#1a1a1a] transition-colors border border-c-border"
              >
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className={`w-3 h-3 rounded-full ${severityColors[mda.maxSeverity]}`} />
                  <span className="text-xs text-gray-500">{mda.findings.length} findings</span>
                </div>
                <h3 className="text-white font-medium mb-2 line-clamp-2">{mda.entity}</h3>
                <div className="text-2xl font-bold text-[#D6453A]">
                  {formatAmount(mda.totalAmount)}
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {mda.findings.slice(0, 3).map((f, idx) => (
                    <span key={idx} className="text-[10px] text-gray-500 bg-[#1a1a1a] px-2 py-0.5 rounded">
                      {f.type?.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {mdaList.map((mda) => (
              <Link
                key={mda.entity}
                href={`/red-flags?search=${encodeURIComponent(mda.entity)}`}
                className="flex items-center justify-between bg-[#111] p-4 hover:bg-[#1a1a1a] transition-colors border border-c-border"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${severityColors[mda.maxSeverity]}`} />
                  <div>
                    <h3 className="text-white font-medium">{mda.entity}</h3>
                    <span className="text-xs text-gray-500">{mda.findings.length} findings</span>
                  </div>
                </div>
                <div className="text-xl font-bold text-[#D6453A]">
                  {formatAmount(mda.totalAmount)}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="bg-[#111] border-t border-c-border px-4 md:px-8 py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-white">{mdaList.length}</div>
            <div className="text-xs text-gray-500">MDAs FLAGGED</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-[#D6453A]">{totalFindings}</div>
            <div className="text-xs text-gray-500">TOTAL FINDINGS</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-[#EBC346]">{formatAmount(totalAmount)}</div>
            <div className="text-xs text-gray-500">FLAGGED AMOUNT</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-[#487A3A]">{states.length + 1}</div>
            <div className="text-xs text-gray-500">JURISDICTIONS</div>
          </div>
        </div>
      </div>
    </div>
  );
}
