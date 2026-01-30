"use client";

import { Search, TrendingUp, AlertTriangle, Share2 } from "lucide-react";

export function Hero() {
  return (
    <section className="p-4 md:p-6 border-b border-gray-800">
      {/* Main headline */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-4xl font-bold leading-tight mb-3">
          See where Nigeria&apos;s{" "}
          <span className="text-[#25D366]">₦28.7 trillion</span>{" "}
          budget really goes
        </h1>
        <p className="text-gray-400 text-sm md:text-base leading-relaxed max-w-2xl">
          We analyzed 2,790 pages of the 2026 federal budget and found{" "}
          <span className="text-white font-semibold">₦86 billion</span> in suspicious spending.
          Search any ministry, ask questions, and share what you find.
        </p>
      </div>

      {/* How it works */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        <div className="border border-gray-800 p-3 hover:border-gray-600 transition-colors">
          <Search className="w-5 h-5 text-[#25D366] mb-2" />
          <h3 className="font-semibold text-sm mb-1">Search</h3>
          <p className="text-xs text-gray-500">
            Ask about any ministry or budget line
          </p>
        </div>

        <div className="border border-gray-800 p-3 hover:border-gray-600 transition-colors">
          <AlertTriangle className="w-5 h-5 text-orange-500 mb-2" />
          <h3 className="font-semibold text-sm mb-1">Discover</h3>
          <p className="text-xs text-gray-500">
            See anomalies flagged by our AI analysis
          </p>
        </div>

        <div className="border border-gray-800 p-3 hover:border-gray-600 transition-colors">
          <TrendingUp className="w-5 h-5 text-blue-500 mb-2" />
          <h3 className="font-semibold text-sm mb-1">Compare</h3>
          <p className="text-xs text-gray-500">
            Compare spending across ministries
          </p>
        </div>

        <div className="border border-gray-800 p-3 hover:border-gray-600 transition-colors">
          <Share2 className="w-5 h-5 text-purple-500 mb-2" />
          <h3 className="font-semibold text-sm mb-1">Share</h3>
          <p className="text-xs text-gray-500">
            Generate cards to spread awareness
          </p>
        </div>
      </div>

      {/* Data source badge */}
      <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
        <span className="w-2 h-2 bg-[#25D366] rounded-full animate-pulse" />
        <span>Data source: 2026 Appropriation Bill (Official Federal Budget)</span>
      </div>
    </section>
  );
}
