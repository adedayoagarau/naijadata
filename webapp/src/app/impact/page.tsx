"use client";

import Link from "next/link";
import ImpactCalculator from "@/components/ImpactCalculator";

export default function ImpactPage() {
  const today = new Date();
  const dateStr = `${String(today.getMonth() + 1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")}.${String(today.getFullYear()).slice(-2)}`;

  // Example outrage amounts
  const outrageExamples = [
    { label: "Vehicle Convoys (2026)", amount: 17_100_000_000 },
    { label: "NASS Travel Allowances", amount: 22_490_000_000 },
    { label: "NIA Hospital Budget", amount: 31_100_000_000 },
    { label: "Miscellaneous Expenses", amount: 5_200_000_000 },
  ];

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
          <Link href="/impact" className="text-white transition-colors">
            IMPACT
          </Link>
          <Link href="/about" className="text-gray-500 hover:text-white transition-colors">
            ABOUT
          </Link>
          <span className="text-gray-600">{dateStr}</span>
        </nav>
      </header>

      {/* Page Title */}
      <div className="bg-[#487A3A] px-4 md:px-8 py-6">
        <h1 className="text-2xl md:text-4xl font-bold text-white">IMPACT CALCULATOR</h1>
        <p className="text-white/70 mt-1">See what government spending could actually build</p>
      </div>

      {/* Main Calculator */}
      <div className="px-4 md:px-8 py-8 max-w-4xl mx-auto">
        <ImpactCalculator showInput={true} maxItems={10} />

        {/* Quick Examples */}
        <div className="mt-8">
          <h3 className="text-white font-bold mb-4">TRY THESE AMOUNTS</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {outrageExamples.map((example) => (
              <button
                key={example.label}
                onClick={() => {
                  // Navigate to same page with amount
                  const url = new URL(window.location.href);
                  url.searchParams.set("amount", example.amount.toString());
                  window.location.href = url.toString();
                }}
                className="bg-[#111] border border-c-border p-3 text-left hover:bg-[#1a1a1a] transition-colors"
              >
                <div className="text-xs text-gray-500 mb-1">{example.label}</div>
                <div className="text-white font-mono">
                  ₦{(example.amount / 1_000_000_000).toFixed(1)}B
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Explanation */}
        <div className="mt-12 bg-[#111] border border-c-border p-6">
          <h3 className="text-white font-bold mb-4">HOW THIS WORKS</h3>
          <div className="space-y-4 text-gray-400 text-sm">
            <p>
              Every Naira in the budget represents a choice. When billions go to convoys and
              travel, that&apos;s billions not going to schools, hospitals, and infrastructure.
            </p>
            <p>
              This calculator uses real Nigerian costs to show what government spending could
              achieve if directed toward public goods:
            </p>
            <ul className="list-disc list-inside space-y-1 text-gray-500">
              <li>
                <span className="text-white">Primary School:</span> ₦150M (6 classrooms, 240
                students)
              </li>
              <li>
                <span className="text-white">Health Center:</span> ₦150M (serves 10,000 people)
              </li>
              <li>
                <span className="text-white">Borehole:</span> ₦5M (clean water for 500 people)
              </li>
              <li>
                <span className="text-white">Ambulance:</span> ₦50M (fully equipped)
              </li>
              <li>
                <span className="text-white">1km Road:</span> ₦150M (paved)
              </li>
            </ul>
            <p className="text-[#EBC346]">
              Use this tool to put budget numbers in context. Share the results to demand
              better priorities.
            </p>
          </div>
        </div>

        {/* API Info */}
        <div className="mt-8 bg-[#0a0a0a] border border-dashed border-gray-700 p-4 rounded">
          <h4 className="text-gray-500 text-xs font-mono mb-2">FOR DEVELOPERS</h4>
          <p className="text-gray-400 text-sm mb-2">
            Use our API to calculate impact programmatically:
          </p>
          <code className="text-[#487A3A] text-xs block bg-black p-2 rounded">
            GET /api/impact?amount=17.1b
          </code>
        </div>
      </div>

      {/* Footer CTA */}
      <div className="bg-[#111] border-t border-c-border px-4 md:px-8 py-8 text-center">
        <h3 className="text-white text-xl font-bold mb-2">Every Naira Counts</h3>
        <p className="text-gray-400 text-sm mb-4 max-w-lg mx-auto">
          When you see a budget number, ask: what could this build instead? Share your
          findings to demand accountability.
        </p>
        <div className="flex justify-center gap-3">
          <Link
            href="/red-flags"
            className="px-6 py-3 bg-[#D6453A] text-white font-mono text-sm uppercase hover:brightness-90"
          >
            View Red Flags
          </Link>
          <Link
            href="/compare"
            className="px-6 py-3 bg-[#EBC346] text-black font-mono text-sm uppercase hover:brightness-90"
          >
            Compare Years
          </Link>
        </div>
      </div>
    </div>
  );
}
