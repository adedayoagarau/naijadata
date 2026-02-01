"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
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
  CRITICAL: "bg-[#D6453A] text-white",
  HIGH: "bg-[#164678] text-white",
  MEDIUM: "bg-[#EBC346] text-black",
  LOW: "bg-[#D9D9CD] text-black",
};

const severityBorder = {
  CRITICAL: "border-l-[#D6453A]",
  HIGH: "border-l-[#164678]",
  MEDIUM: "border-l-[#EBC346]",
  LOW: "border-l-[#D9D9CD]",
};

export default function RedFlagsPage() {
  const searchParams = useSearchParams();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [filteredFindings, setFilteredFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [severity, setSeverity] = useState<string>("ALL");
  const [year, setYear] = useState<string>("ALL");
  const [state, setState] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<string>("severity");

  // Read filters from URL params on mount
  useEffect(() => {
    const urlSearch = searchParams.get("search");
    const urlSeverity = searchParams.get("severity");
    const urlYear = searchParams.get("year");
    const urlState = searchParams.get("state");
    const urlSort = searchParams.get("sort");

    if (urlSearch) setSearch(urlSearch);
    if (urlSeverity) setSeverity(urlSeverity.toUpperCase());
    if (urlYear) setYear(urlYear);
    if (urlState) setState(urlState);
    if (urlSort) setSortBy(urlSort);
  }, [searchParams]);

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

  useEffect(() => {
    let filtered = [...findings];

    if (severity !== "ALL") {
      filtered = filtered.filter((f) => f.severity === severity);
    }
    if (year !== "ALL") {
      filtered = filtered.filter((f) => f.year === parseInt(year));
    }
    if (state !== "ALL") {
      if (state === "FEDERAL") {
        filtered = filtered.filter((f) => !f.state);
      } else {
        filtered = filtered.filter((f) => f.state === state);
      }
    }
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (f) =>
          f.entity?.toLowerCase().includes(q) ||
          f.description?.toLowerCase().includes(q) ||
          f.type?.toLowerCase().includes(q)
      );
    }

    // Sort
    const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    if (sortBy === "severity") {
      filtered.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
    } else if (sortBy === "amount") {
      filtered.sort((a, b) => (b.amount || 0) - (a.amount || 0));
    } else if (sortBy === "year") {
      filtered.sort((a, b) => b.year - a.year);
    }

    setFilteredFindings(filtered);
  }, [severity, year, state, search, sortBy, findings]);

  const years = [...new Set(findings.map((f) => f.year))].sort((a, b) => b - a);
  const states = [...new Set(findings.map((f) => f.state).filter(Boolean))].sort() as string[];
  const totalFlagged = filteredFindings.reduce((sum, f) => sum + (f.amount || 0), 0);

  const today = new Date();
  const dateStr = `${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}.${String(today.getFullYear()).slice(-2)}`;

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
          <Link href="/red-flags" className="text-white transition-colors">
            RED FLAGS ({findings.length})
          </Link>
          <Link href="/compare" className="text-gray-500 hover:text-white transition-colors">
            COMPARE
          </Link>
          <Link href="/explore" className="text-gray-500 hover:text-white transition-colors">
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
      <div className="bg-[#D6453A] px-4 md:px-8 py-6">
        <h1 className="text-2xl md:text-4xl font-bold text-black">RED FLAGS</h1>
        <p className="text-black/70 mt-1">
          {filteredFindings.length} anomalies worth {formatAmount(totalFlagged)}
        </p>
      </div>

      {/* Filters */}
      <div className="bg-c-black border-b border-c-border px-4 md:px-8 py-4 flex flex-wrap gap-3 items-center">
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="bg-transparent border border-gray-600 text-white text-xs px-3 py-2 rounded"
        >
          <option value="ALL">All Severity</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select
          value={year}
          onChange={(e) => setYear(e.target.value)}
          className="bg-transparent border border-gray-600 text-white text-xs px-3 py-2 rounded"
        >
          <option value="ALL">All Years</option>
          {years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>

        <select
          value={state}
          onChange={(e) => setState(e.target.value)}
          className="bg-transparent border border-gray-600 text-white text-xs px-3 py-2 rounded"
        >
          <option value="ALL">All States</option>
          <option value="FEDERAL">Federal</option>
          {states.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-transparent border border-gray-600 text-white text-xs px-3 py-2 rounded"
        >
          <option value="severity">Sort by Severity</option>
          <option value="amount">Sort by Amount</option>
          <option value="year">Sort by Year</option>
        </select>

        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent border border-gray-600 text-white text-xs px-3 py-2 rounded flex-1 min-w-[150px] placeholder:text-gray-500"
        />
      </div>

      {/* Findings List */}
      <div className="px-4 md:px-8 py-6">
        {loading ? (
          <div className="text-center text-gray-500 py-12">Loading findings...</div>
        ) : filteredFindings.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <p className="text-lg">No findings match your filters</p>
            <p className="text-sm mt-2">Try adjusting your search criteria</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredFindings.map((finding) => (
              <Link
                key={finding.id}
                href={`/finding/${finding.id}`}
                className={`block bg-[#111] border-l-4 ${severityBorder[finding.severity]} p-4 md:p-6 hover:bg-[#1a1a1a] transition-colors`}
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-1 text-[10px] font-mono uppercase ${severityColors[finding.severity]}`}>
                        {finding.severity}
                      </span>
                      <span className="text-gray-500 text-xs">
                        {finding.type?.replace(/_/g, " ")}
                      </span>
                    </div>
                    <h3 className="text-white text-lg md:text-xl font-medium mb-1">
                      {finding.entity}
                    </h3>
                    <p className="text-gray-400 text-sm line-clamp-2">
                      {finding.description}
                    </p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                      <span>{finding.year}</span>
                      {finding.state && <span>{finding.state}</span>}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl md:text-3xl font-bold text-[#D6453A]">
                      {formatAmount(finding.amount)}
                    </div>
                    {finding.risk_score && (
                      <div className="text-xs text-gray-500 mt-1">
                        Risk: {finding.risk_score}/100
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
