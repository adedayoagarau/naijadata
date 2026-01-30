"use client";

import { useState } from "react";
import { Share2, ChevronRight, Download, Zap } from "lucide-react";

interface Discovery {
  id: string;
  type: "comparison" | "stat" | "redflag" | "impact";
  tag: string;
  tagColor: string;
  title: string;
  subtitle?: string;
  stat1?: { label: string; value: string };
  stat2?: { label: string; value: string };
  highlight: string;
  highlightColor: string;
  description: string;
  impact?: string[];
  shareText: string;
}

const discoveries: Discovery[] = [
  {
    id: "nia-health",
    type: "comparison",
    tag: "SCANDAL",
    tagColor: "bg-red-600",
    title: "SPY AGENCY VS HEALTH MINISTRY",
    stat1: { label: "NIA Hospital Budget", value: "₦31.1B" },
    stat2: { label: "Health Ministry Hospitals", value: "₦675M" },
    highlight: "46X MORE",
    highlightColor: "bg-white text-black",
    description: "The National Intelligence Agency is spending 46 times more on hospital repairs than the actual Health Ministry headquarters.",
    impact: ["207 health centers", "6,220 boreholes", "622 ambulances"],
    shareText: "Nigeria's spy agency (NIA) is spending ₦31.1B on hospitals - 46x more than the Health Ministry! #Decide9ja",
  },
  {
    id: "nass-cost",
    type: "stat",
    tag: "AUDIT",
    tagColor: "bg-yellow-600",
    title: "COST PER LEGISLATOR",
    stat1: { label: "Per Lawmaker (469 total)", value: "₦735M" },
    highlight: "4,900 YEARS",
    highlightColor: "bg-[#25D366] text-black",
    description: "Each Nigerian legislator costs ₦735 million per year. That's equivalent to 4,900 years of minimum wage.",
    impact: ["4 primary schools", "4 health centers", "147 boreholes"],
    shareText: "Each Nigerian lawmaker costs ₦735M/year - that's 4,900 YEARS of minimum wage! #Decide9ja",
  },
  {
    id: "police-meals",
    type: "redflag",
    tag: "ANOMALY",
    tagColor: "bg-orange-600",
    title: "POLICE ACADEMY FEEDING SCHOOLS",
    stat1: { label: "Police Academy Wudil", value: "₦5.9B" },
    stat2: { label: "For: School Meal Subsidies", value: "???" },
    highlight: "WRONG MINISTRY",
    highlightColor: "bg-red-600 text-white",
    description: "Nigeria Police Academy is budgeting ₦5.9 billion for school meal subsidies. This should be under Education, not Police.",
    impact: ["39 primary schools", "1,180 boreholes"],
    shareText: "Why is a Police Academy spending ₦5.9B on school meals? Wrong ministry! #Decide9ja",
  },
  {
    id: "nass-travel",
    type: "comparison",
    tag: "TRAVEL",
    tagColor: "bg-blue-600",
    title: "NASS TRAVEL BUDGET",
    stat1: { label: "National Assembly Travel", value: "₦22.49B" },
    stat2: { label: "Health Drugs (10M Nigerians)", value: "₦42.2B" },
    highlight: "53% OF DRUGS BUDGET",
    highlightColor: "bg-white text-black",
    description: "The National Assembly's travel budget alone is more than half of what Health spends on drugs for 10 million Nigerians.",
    impact: ["150 primary schools", "4,498 boreholes", "449 ambulances"],
    shareText: "NASS travel budget (₦22.49B) is 53% of what Health spends on drugs for 10M Nigerians! #Decide9ja",
  },
  {
    id: "army-roads",
    type: "redflag",
    tag: "MANDATE",
    tagColor: "bg-purple-600",
    title: "ARMY BUILDING ROADS",
    stat1: { label: "Nigerian Army", value: "₦3.72B" },
    stat2: { label: "For: Road Construction", value: "Works Ministry?" },
    highlight: "OUTSIDE MANDATE",
    highlightColor: "bg-orange-600 text-white",
    description: "The Nigerian Army has ₦3.72 billion for road construction. This should be under the Federal Ministry of Works.",
    impact: ["24 km of paved roads", "744 boreholes"],
    shareText: "Why is the Army building roads? ₦3.72B that should be under Works Ministry! #Decide9ja",
  },
  {
    id: "total-anomalies",
    type: "stat",
    tag: "SUMMARY",
    tagColor: "bg-[#25D366]",
    title: "TOTAL SUSPICIOUS SPENDING",
    stat1: { label: "Cross-MDA Anomalies", value: "₦86B" },
    stat2: { label: "Red Flags Found", value: "177" },
    highlight: "₦86 BILLION",
    highlightColor: "bg-red-600 text-white",
    description: "Our analysis found 177 red flags totaling ₦86 billion in suspicious cross-MDA spending in the 2026 budget.",
    impact: ["573 primary schools", "17,200 boreholes", "1,720 ambulances"],
    shareText: "We found ₦86 BILLION in suspicious spending across 177 red flags in Nigeria's 2026 budget! #Decide9ja",
  },
];

export function DiscoveryFeed() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleShare = async (discovery: Discovery) => {
    if (navigator.share) {
      await navigator.share({
        title: discovery.title,
        text: discovery.shareText,
        url: window.location.href,
      });
    } else {
      // Fallback: copy to clipboard
      await navigator.clipboard.writeText(discovery.shareText + " " + window.location.href);
      alert("Copied to clipboard!");
    }
  };

  const handleGenerateCard = async (discovery: Discovery) => {
    try {
      const response = await fetch("/api/card", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: discovery.title,
          amount: discovery.stat1?.value || "",
          description: discovery.description,
          comparison: discovery.highlight,
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `decide9ja-${discovery.id}.png`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Error generating card:", error);
    }
  };

  return (
    <section className="p-4 border-b border-white">
      <div className="flex justify-between items-end mb-4">
        <div>
          <h3 className="font-pixel text-2xl md:text-3xl flex items-center gap-2">
            <Zap className="w-6 h-6 text-[#25D366]" />
            DISCOVERIES
          </h3>
          <p className="text-[10px] text-gray-500 uppercase mt-1">
            Tap any card to share • Swipe for more
          </p>
        </div>
        <div className="text-[10px] font-mono text-[#25D366]">
          {discoveries.length} FINDINGS
        </div>
      </div>

      <div className="space-y-4">
        {discoveries.map((discovery) => (
          <div
            key={discovery.id}
            className="border border-white bg-[#0a0a0a] relative overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] px-2 py-0.5 font-bold ${discovery.tagColor}`}>
                  {discovery.tag}
                </span>
                <span className="text-[10px] text-gray-500">#{discovery.id}</span>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => handleShare(discovery)}
                  className="w-8 h-8 border border-gray-700 flex items-center justify-center hover:bg-white hover:text-black transition-colors"
                >
                  <Share2 size={14} />
                </button>
                <button
                  onClick={() => handleGenerateCard(discovery)}
                  className="w-8 h-8 border border-gray-700 flex items-center justify-center hover:bg-[#25D366] hover:text-black transition-colors"
                >
                  <Download size={14} />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-4">
              <h4 className="font-bold font-mono text-lg mb-3">{discovery.title}</h4>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 mb-3">
                {discovery.stat1 && (
                  <div className="border border-gray-800 p-2">
                    <div className="text-[10px] text-gray-500 uppercase">{discovery.stat1.label}</div>
                    <div className="font-pixel text-2xl text-white">{discovery.stat1.value}</div>
                  </div>
                )}
                {discovery.stat2 && (
                  <div className="border border-gray-800 p-2">
                    <div className="text-[10px] text-gray-500 uppercase">{discovery.stat2.label}</div>
                    <div className="font-pixel text-2xl text-white">{discovery.stat2.value}</div>
                  </div>
                )}
              </div>

              {/* Highlight */}
              <div className={`inline-block px-3 py-1 font-bold font-mono text-lg mb-3 ${discovery.highlightColor}`}>
                {discovery.highlight}
              </div>

              {/* Description */}
              <p className="text-sm text-gray-400 leading-relaxed mb-3">
                {discovery.description}
              </p>

              {/* Impact */}
              {discovery.impact && (
                <div className="border-t border-gray-800 pt-3">
                  <div className="text-[10px] text-gray-500 uppercase mb-2">This could build:</div>
                  <div className="flex flex-wrap gap-2">
                    {discovery.impact.map((item, i) => (
                      <span key={i} className="text-xs bg-[#111] border border-gray-800 px-2 py-1">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Action bar */}
            <div className="flex border-t border-gray-800">
              <button
                onClick={() => handleShare(discovery)}
                className="flex-1 py-3 text-xs font-mono uppercase flex items-center justify-center gap-2 hover:bg-[#25D366] hover:text-black transition-colors border-r border-gray-800"
              >
                <Share2 size={14} /> SHARE
              </button>
              <button
                onClick={() => handleGenerateCard(discovery)}
                className="flex-1 py-3 text-xs font-mono uppercase flex items-center justify-center gap-2 hover:bg-white hover:text-black transition-colors"
              >
                <Download size={14} /> DOWNLOAD CARD
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
