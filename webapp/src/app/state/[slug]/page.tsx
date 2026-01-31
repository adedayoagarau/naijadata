"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { governors, getGovernorByState, partyColors, partyFullNames, Governor } from "@/data/governors";

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

export default function StatePage() {
  const params = useParams();
  const slug = params.slug as string;

  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

  const governor = getGovernorByState(slug);

  useEffect(() => {
    const loadFindings = async () => {
      try {
        const res = await fetch("/api/findings");
        if (res.ok) {
          const data = await res.json();
          // Filter findings for this state
          const stateFindings = (data.findings || []).filter(
            (f: Finding) => f.state?.toLowerCase().replace(/\s+/g, "-") === slug.toLowerCase()
          );
          setFindings(stateFindings);
        }
      } catch (err) {
        console.error("Failed to load findings:", err);
      } finally {
        setLoading(false);
      }
    };
    loadFindings();
  }, [slug]);

  const today = new Date();
  const dateStr = `${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}.${String(today.getFullYear()).slice(-2)}`;

  const totalAmount = findings.reduce((sum, f) => sum + (f.amount || 0), 0);
  const criticalCount = findings.filter((f) => f.severity === "CRITICAL").length;
  const highCount = findings.filter((f) => f.severity === "HIGH").length;

  // Get state name from slug or governor data
  const stateName = governor?.state || slug.split("-").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");

  return (
    <div
      className="min-h-screen bg-c-black"
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
            RED FLAGS
          </Link>
          <Link href="/explore" className="text-gray-500 hover:text-white transition-colors">
            EXPLORE
          </Link>
          <Link href="/about" className="text-gray-500 hover:text-white transition-colors">
            ABOUT
          </Link>
          <span className="text-gray-600">{dateStr}</span>
        </nav>
      </header>

      {/* State Header */}
      <div
        className="px-4 md:px-8 py-8"
        style={{ backgroundColor: governor ? partyColors[governor.party] : "#164678" }}
      >
        <div className="flex flex-col md:flex-row gap-6 items-start md:items-center max-w-6xl">
          {/* Governor Avatar Placeholder */}
          <div className="w-24 h-24 md:w-32 md:h-32 bg-white/20 rounded-full flex items-center justify-center text-4xl font-bold text-white/50">
            {governor?.name.charAt(0) || "?"}
          </div>

          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
              {stateName} State
            </h1>
            {governor && (
              <>
                <p className="text-white/80 text-lg mb-1">
                  Governor: <span className="font-medium">{governor.name}</span>
                </p>
                <p className="text-white/60 text-sm">
                  {partyFullNames[governor.party]} ({governor.party}) • Since {governor.since}
                </p>
              </>
            )}
          </div>

          {/* Quick Stats */}
          <div className="flex gap-4 md:gap-6">
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-white">{findings.length}</div>
              <div className="text-xs text-white/60">Findings</div>
            </div>
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-white">{formatAmount(totalAmount)}</div>
              <div className="text-xs text-white/60">Flagged</div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="bg-[#111] border-b border-c-border px-4 md:px-8 py-4">
        <div className="flex gap-6 text-sm font-mono max-w-6xl">
          <span className="text-[#D6453A]">
            <span className="text-gray-500">CRITICAL:</span> {criticalCount}
          </span>
          <span className="text-[#164678]">
            <span className="text-gray-500">HIGH:</span> {highCount}
          </span>
          <span className="text-gray-400">
            <span className="text-gray-500">TOTAL:</span> {findings.length}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 md:px-8 py-8 max-w-6xl">
        {loading ? (
          <div className="text-center text-gray-500 py-12">Loading state data...</div>
        ) : findings.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">No findings for {stateName} State yet</div>
            <p className="text-gray-600 text-sm mb-6">
              We&apos;re still collecting and analyzing budget data for this state.
            </p>
            <Link
              href="/explore"
              className="inline-block bg-[#164678] text-white px-6 py-3 font-mono text-sm uppercase hover:brightness-90 transition-colors"
            >
              Explore Other States
            </Link>
          </div>
        ) : (
          <>
            <h2 className="text-white font-bold text-xl mb-6">Budget Findings</h2>
            <div className="space-y-4">
              {findings.map((finding) => (
                <Link
                  key={finding.id}
                  href={`/finding/${finding.id}`}
                  className="block bg-[#111] border border-c-border p-4 md:p-6 hover:bg-[#1a1a1a] transition-colors"
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
                      <h3 className="text-white text-lg font-medium mb-1">
                        {finding.entity}
                      </h3>
                      <p className="text-gray-400 text-sm line-clamp-2">
                        {finding.description}
                      </p>
                      <div className="mt-2 text-xs text-gray-500">
                        {finding.year}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-[#D6453A]">
                        {formatAmount(finding.amount)}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </>
        )}

        {/* Other States Navigation */}
        <div className="mt-12 pt-8 border-t border-c-border">
          <h3 className="text-white font-bold mb-4">OTHER STATES</h3>
          <div className="flex flex-wrap gap-2">
            {governors
              .filter((g) => g.slug !== slug)
              .slice(0, 12)
              .map((g) => (
                <Link
                  key={g.slug}
                  href={`/state/${g.slug}`}
                  className="px-3 py-1 bg-[#111] text-gray-400 text-xs rounded hover:bg-[#1a1a1a] hover:text-white transition-colors"
                >
                  {g.state}
                </Link>
              ))}
            <Link
              href="/explore"
              className="px-3 py-1 bg-[#164678] text-white text-xs rounded hover:brightness-90 transition-colors"
            >
              View All →
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-[#111] border-t border-c-border px-4 md:px-8 py-6 mt-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-500 max-w-6xl">
          <div>
            Decide9ja © {new Date().getFullYear()} — Budget Transparency for Nigeria
          </div>
          <div className="flex gap-4">
            <Link href="/red-flags" className="hover:text-white transition-colors">Red Flags</Link>
            <Link href="/explore" className="hover:text-white transition-colors">Explore</Link>
            <Link href="/about" className="hover:text-white transition-colors">About</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
