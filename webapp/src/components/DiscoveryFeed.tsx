"use client";

import { useState } from "react";
import { Share2, Download, Zap, Loader2, ChevronLeft, ChevronRight } from "lucide-react";

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
    tag: "Scandal",
    tagColor: "bg-red-600",
    title: "Spy Agency vs Health Ministry",
    stat1: { label: "NIA Hospital Budget", value: "₦31.1B" },
    stat2: { label: "Health Ministry Hospitals", value: "₦675M" },
    highlight: "46× more",
    highlightColor: "bg-white text-black",
    description: "The National Intelligence Agency is spending 46 times more on hospital repairs than the actual Health Ministry headquarters.",
    impact: ["207 health centers", "6,220 boreholes", "622 ambulances"],
    shareText: "Nigeria's spy agency (NIA) is spending ₦31.1B on hospitals - 46x more than the Health Ministry! #Decide9ja",
  },
  {
    id: "nass-cost",
    type: "stat",
    tag: "Audit",
    tagColor: "bg-yellow-600",
    title: "Cost per Legislator",
    stat1: { label: "Per Lawmaker (469 total)", value: "₦735M" },
    highlight: "4,900 years",
    highlightColor: "bg-[#25D366] text-black",
    description: "Each Nigerian legislator costs ₦735 million per year. That's equivalent to 4,900 years of minimum wage for an average worker.",
    impact: ["4 primary schools", "4 health centers", "147 boreholes"],
    shareText: "Each Nigerian lawmaker costs ₦735M/year - that's 4,900 YEARS of minimum wage! #Decide9ja",
  },
  {
    id: "police-meals",
    type: "redflag",
    tag: "Anomaly",
    tagColor: "bg-orange-600",
    title: "Police Academy Feeding Schools",
    stat1: { label: "Police Academy Wudil", value: "₦5.9B" },
    stat2: { label: "Budget line", value: "School Meals" },
    highlight: "Wrong ministry",
    highlightColor: "bg-red-600 text-white",
    description: "Nigeria Police Academy is budgeting ₦5.9 billion for school meal subsidies. This should be under Education, not Police.",
    impact: ["39 primary schools", "1,180 boreholes"],
    shareText: "Why is a Police Academy spending ₦5.9B on school meals? Wrong ministry! #Decide9ja",
  },
  {
    id: "nass-travel",
    type: "comparison",
    tag: "Travel",
    tagColor: "bg-blue-600",
    title: "National Assembly Travel Budget",
    stat1: { label: "NASS Travel", value: "₦22.49B" },
    stat2: { label: "Health Drugs Budget", value: "₦42.2B" },
    highlight: "53% of drugs budget",
    highlightColor: "bg-white text-black",
    description: "The National Assembly's travel budget alone is more than half of what Health spends on drugs for 10 million Nigerians.",
    impact: ["150 primary schools", "4,498 boreholes", "449 ambulances"],
    shareText: "NASS travel budget (₦22.49B) is 53% of what Health spends on drugs for 10M Nigerians! #Decide9ja",
  },
  {
    id: "army-roads",
    type: "redflag",
    tag: "Mandate",
    tagColor: "bg-purple-600",
    title: "Army Building Roads",
    stat1: { label: "Nigerian Army", value: "₦3.72B" },
    stat2: { label: "Budget line", value: "Road Construction" },
    highlight: "Outside mandate",
    highlightColor: "bg-orange-600 text-white",
    description: "The Nigerian Army has ₦3.72 billion for road construction. This should be under the Federal Ministry of Works.",
    impact: ["24 km of paved roads", "744 boreholes"],
    shareText: "Why is the Army building roads? ₦3.72B that should be under Works Ministry! #Decide9ja",
  },
  {
    id: "total-anomalies",
    type: "stat",
    tag: "Summary",
    tagColor: "bg-[#25D366]",
    title: "Total Suspicious Spending",
    stat1: { label: "Cross-MDA Anomalies", value: "₦86B" },
    stat2: { label: "Red Flags Found", value: "177" },
    highlight: "₦86 billion",
    highlightColor: "bg-red-600 text-white",
    description: "Our analysis found 177 red flags totaling ₦86 billion in suspicious cross-MDA spending in the 2026 budget.",
    impact: ["573 primary schools", "17,200 boreholes", "1,720 ambulances"],
    shareText: "We found ₦86 BILLION in suspicious spending across 177 red flags in Nigeria's 2026 budget! #Decide9ja",
  },
];

interface ToastState {
  show: boolean;
  message: string;
  type: "success" | "error" | "loading";
}

export function DiscoveryFeed() {
  const [loadingStates, setLoadingStates] = useState<Record<string, "share" | "download" | null>>({});
  const [toast, setToast] = useState<ToastState>({ show: false, message: "", type: "success" });

  const showToast = (message: string, type: "success" | "error" | "loading") => {
    setToast({ show: true, message, type });
    if (type !== "loading") {
      setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
    }
  };

  const handleShare = async (discovery: Discovery) => {
    setLoadingStates((prev) => ({ ...prev, [discovery.id]: "share" }));

    try {
      if (navigator.share) {
        await navigator.share({
          title: discovery.title,
          text: discovery.shareText,
          url: window.location.href,
        });
        showToast("Shared successfully!", "success");
      } else {
        await navigator.clipboard.writeText(discovery.shareText + " " + window.location.href);
        showToast("Copied to clipboard!", "success");
      }
    } catch (error: unknown) {
      if (error instanceof Error && error.name !== "AbortError") {
        showToast("Failed to share", "error");
      }
    } finally {
      setLoadingStates((prev) => ({ ...prev, [discovery.id]: null }));
    }
  };

  const handleGenerateCard = async (discovery: Discovery) => {
    setLoadingStates((prev) => ({ ...prev, [discovery.id]: "download" }));
    showToast("Generating card...", "loading");

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
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast("Card downloaded!", "success");
      } else {
        throw new Error("Failed to generate");
      }
    } catch (error) {
      console.error("Error generating card:", error);
      showToast("Failed to generate card", "error");
    } finally {
      setLoadingStates((prev) => ({ ...prev, [discovery.id]: null }));
    }
  };

  return (
    <section className="p-4 border-b border-gray-800">
      {/* Toast notification */}
      {toast.show && (
        <div
          className={`fixed bottom-24 left-4 right-4 md:left-auto md:right-4 md:w-80 z-[60]
            border p-4 flex items-center gap-3 shadow-lg bg-[#0a0a0a]
            ${toast.type === "success" ? "border-[#25D366]" : ""}
            ${toast.type === "error" ? "border-red-500" : ""}
            ${toast.type === "loading" ? "border-gray-500" : ""}`}
          role="alert"
        >
          {toast.type === "loading" && <Loader2 className="w-5 h-5 animate-spin" />}
          {toast.type === "success" && <span className="text-[#25D366]">✓</span>}
          {toast.type === "error" && <span className="text-red-500">✗</span>}
          <span className="text-sm">{toast.message}</span>
        </div>
      )}

      <div className="flex justify-between items-end mb-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold flex items-center gap-2">
            <Zap className="w-5 h-5 text-[#25D366]" />
            Budget Discoveries
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            {discoveries.length} findings from 2026 federal budget analysis
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {discoveries.map((discovery) => {
          const isLoading = loadingStates[discovery.id];

          return (
            <article
              key={discovery.id}
              className="border border-gray-800 bg-[#0a0a0a] relative overflow-hidden hover:border-gray-600 transition-colors"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-3 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] px-2 py-0.5 font-semibold ${discovery.tagColor}`}
                  >
                    {discovery.tag}
                  </span>
                  <span className="text-[10px] text-gray-600">#{discovery.id}</span>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleShare(discovery)}
                    disabled={!!isLoading}
                    className="w-8 h-8 border border-gray-700 flex items-center justify-center
                      hover:bg-white hover:text-black transition-colors disabled:opacity-50"
                    aria-label={`Share ${discovery.title}`}
                  >
                    {isLoading === "share" ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Share2 size={14} />
                    )}
                  </button>
                  <button
                    onClick={() => handleGenerateCard(discovery)}
                    disabled={!!isLoading}
                    className="w-8 h-8 border border-gray-700 flex items-center justify-center
                      hover:bg-[#25D366] hover:text-black transition-colors disabled:opacity-50"
                    aria-label={`Download card for ${discovery.title}`}
                  >
                    {isLoading === "download" ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Download size={14} />
                    )}
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-bold text-lg mb-3">{discovery.title}</h3>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-3 mb-3">
                  {discovery.stat1 && (
                    <div className="border border-gray-800 p-3 bg-[#111]">
                      <div className="text-[10px] text-gray-500 mb-1">
                        {discovery.stat1.label}
                      </div>
                      <div className="font-mono text-xl md:text-2xl text-white font-bold">
                        {discovery.stat1.value}
                      </div>
                    </div>
                  )}
                  {discovery.stat2 && (
                    <div className="border border-gray-800 p-3 bg-[#111]">
                      <div className="text-[10px] text-gray-500 mb-1">
                        {discovery.stat2.label}
                      </div>
                      <div className="font-mono text-xl md:text-2xl text-white font-bold">
                        {discovery.stat2.value}
                      </div>
                    </div>
                  )}
                </div>

                {/* Highlight */}
                <div
                  className={`inline-block px-3 py-1.5 font-bold text-base mb-3 ${discovery.highlightColor}`}
                >
                  {discovery.highlight}
                </div>

                {/* Description */}
                <p className="text-sm text-gray-400 leading-relaxed mb-3">
                  {discovery.description}
                </p>

                {/* Impact */}
                {discovery.impact && (
                  <div className="border-t border-gray-800 pt-3">
                    <div className="text-[10px] text-gray-500 mb-2">
                      This amount could build:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {discovery.impact.map((item, i) => (
                        <span
                          key={i}
                          className="text-xs bg-[#111] border border-gray-800 px-2 py-1 text-gray-300"
                        >
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
                  disabled={!!isLoading}
                  className="flex-1 py-3 text-xs font-medium flex items-center justify-center gap-2
                    hover:bg-[#25D366] hover:text-black transition-colors border-r border-gray-800
                    disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label={`Share ${discovery.title}`}
                >
                  {isLoading === "share" ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Share2 size={14} />
                  )}
                  Share
                </button>
                <button
                  onClick={() => handleGenerateCard(discovery)}
                  disabled={!!isLoading}
                  className="flex-1 py-3 text-xs font-medium flex items-center justify-center gap-2
                    hover:bg-white hover:text-black transition-colors
                    disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label={`Download card for ${discovery.title}`}
                >
                  {isLoading === "download" ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Download size={14} />
                  )}
                  Download Card
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
