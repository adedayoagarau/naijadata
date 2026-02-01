"use client";

import Link from "next/link";

export default function AboutPage() {
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
          <Link href="/red-flags" className="text-gray-500 hover:text-white transition-colors">
            RED FLAGS
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
          <Link href="/about" className="text-white transition-colors">
            ABOUT
          </Link>
          <span className="text-gray-600">{dateStr}</span>
        </nav>
      </header>

      {/* Page Title */}
      <div className="bg-[#487A3A] px-4 md:px-8 py-6">
        <h1 className="text-2xl md:text-4xl font-bold text-white">ABOUT DECIDE9JA</h1>
        <p className="text-white/70 mt-1">
          See where your money goes
        </p>
      </div>

      {/* Content */}
      <div className="px-4 md:px-8 py-8 max-w-4xl">
        {/* Mission */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-white mb-4 border-b border-c-border pb-2">
            OUR MISSION
          </h2>
          <p className="text-gray-300 leading-relaxed mb-4">
            Decide9ja is a budget transparency and accountability tool built for Nigerians.
            We analyze federal and state budgets to identify anomalies, suspicious spending patterns,
            and potential areas of concern that deserve public scrutiny.
          </p>
          <p className="text-gray-300 leading-relaxed">
            Our goal is to empower citizens with data-driven insights into how public funds
            are allocated and spent, making government more accountable to the people it serves.
          </p>
        </section>

        {/* How It Works */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-white mb-4 border-b border-c-border pb-2">
            HOW IT WORKS
          </h2>
          <div className="space-y-6">
            <div className="flex gap-4">
              <div className="w-8 h-8 bg-[#D6453A] text-black font-bold flex items-center justify-center flex-shrink-0">
                1
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Data Collection</h3>
                <p className="text-gray-400 text-sm">
                  We collect budget documents from federal and state government sources,
                  including appropriation bills, budget breakdowns, and financial reports.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-8 h-8 bg-[#EBC346] text-black font-bold flex items-center justify-center flex-shrink-0">
                2
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">AI Analysis</h3>
                <p className="text-gray-400 text-sm">
                  Our AI-powered system analyzes budget line items, looking for patterns
                  such as unusual year-over-year changes, mandate violations, round number
                  allocations, and cross-MDA outliers.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-8 h-8 bg-[#164678] text-white font-bold flex items-center justify-center flex-shrink-0">
                3
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Red Flag Detection</h3>
                <p className="text-gray-400 text-sm">
                  Anomalies are flagged and categorized by severity (Critical, High, Medium, Low)
                  based on the nature and magnitude of the finding.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-8 h-8 bg-[#487A3A] text-white font-bold flex items-center justify-center flex-shrink-0">
                4
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Public Access</h3>
                <p className="text-gray-400 text-sm">
                  All findings are made available through this platform, with tools for
                  searching, filtering, and sharing information on social media.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Detection Methods */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-white mb-4 border-b border-c-border pb-2">
            WHAT WE DETECT
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#111] p-4 border border-c-border">
              <h3 className="text-[#D6453A] font-mono text-sm mb-2">MANDATE_VIOLATION</h3>
              <p className="text-gray-400 text-sm">
                When an agency spends on activities outside its core mandate
                (e.g., a security agency building hospitals)
              </p>
            </div>
            <div className="bg-[#111] p-4 border border-c-border">
              <h3 className="text-[#D6453A] font-mono text-sm mb-2">YOY_VARIANCE</h3>
              <p className="text-gray-400 text-sm">
                Unusual year-over-year changes in budget allocations
                (e.g., 300% increase in travel allowances)
              </p>
            </div>
            <div className="bg-[#111] p-4 border border-c-border">
              <h3 className="text-[#EBC346] font-mono text-sm mb-2">ROUND_NUMBER</h3>
              <p className="text-gray-400 text-sm">
                Suspiciously round allocations that suggest estimation
                rather than actual costing
              </p>
            </div>
            <div className="bg-[#111] p-4 border border-c-border">
              <h3 className="text-[#D6453A] font-mono text-sm mb-2">CROSS_MDA_OUTLIER</h3>
              <p className="text-gray-400 text-sm">
                When one agency spends significantly more than others
                on similar budget items
              </p>
            </div>
            <div className="bg-[#111] p-4 border border-c-border">
              <h3 className="text-[#164678] font-mono text-sm mb-2">BENFORD_VIOLATION</h3>
              <p className="text-gray-400 text-sm">
                First digit distribution that deviates from Benford&apos;s Law,
                indicating potential data manipulation
              </p>
            </div>
            <div className="bg-[#111] p-4 border border-c-border">
              <h3 className="text-[#164678] font-mono text-sm mb-2">PADDING_INDICATOR</h3>
              <p className="text-gray-400 text-sm">
                Costs significantly above market benchmarks
                (e.g., vehicles at 450% market price)
              </p>
            </div>
          </div>
        </section>

        {/* Data Sources */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-white mb-4 border-b border-c-border pb-2">
            DATA SOURCES
          </h2>
          <ul className="text-gray-300 space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-[#487A3A]">•</span>
              Federal Budget Office of Nigeria
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#487A3A]">•</span>
              State Budget Appropriation Bills (36 States + FCT)
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#487A3A]">•</span>
              National Assembly Budget Documents
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#487A3A]">•</span>
              Office of the Accountant General
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#487A3A]">•</span>
              Public Procurement Portal
            </li>
          </ul>
        </section>

        {/* Disclaimer */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-white mb-4 border-b border-c-border pb-2">
            DISCLAIMER
          </h2>
          <div className="bg-[#111] p-4 border-l-4 border-[#EBC346]">
            <p className="text-gray-400 text-sm leading-relaxed">
              The findings presented on Decide9ja are generated through automated analysis
              and are intended to highlight potential areas of concern for further investigation.
              A flagged item does not constitute evidence of wrongdoing. We encourage users
              to verify information through official channels and engage constructively in
              budget oversight processes.
            </p>
          </div>
        </section>

        {/* Contact */}
        <section>
          <h2 className="text-xl font-bold text-white mb-4 border-b border-c-border pb-2">
            GET INVOLVED
          </h2>
          <p className="text-gray-300 mb-4">
            Decide9ja is an open civic technology project. We welcome contributions,
            feedback, and collaboration from citizens, journalists, researchers, and
            civil society organizations.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="https://twitter.com/decide9ja"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-c-black border border-gray-600 text-white px-4 py-2 text-sm hover:bg-[#111] transition-colors"
            >
              Follow on X
            </a>
            <a
              href="mailto:hello@decide9ja.ng"
              className="bg-[#487A3A] text-white px-4 py-2 text-sm hover:brightness-90 transition-colors"
            >
              Contact Us
            </a>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="bg-[#111] border-t border-c-border px-4 md:px-8 py-6 mt-12">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-500">
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
