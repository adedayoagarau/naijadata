"use client";

import { useState } from "react";
import { Share2, Download, Loader2, ArrowRight, ExternalLink } from "lucide-react";

interface Discovery {
  id: string;
  tag: string;
  tagColor: string;
  title: string;
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
    tag: "Scandal",
    tagColor: "bg-red-500/20 text-red-400",
    title: "Spy Agency vs Health Ministry",
    stat1: { label: "NIA Hospital Budget", value: "₦31.1B" },
    stat2: { label: "Health Ministry", value: "₦675M" },
    highlight: "46× more",
    highlightColor: "bg-red-500 text-white",
    description: "The National Intelligence Agency is spending 46 times more on hospital repairs than the actual Health Ministry.",
    impact: ["207 health centers", "6,220 boreholes", "622 ambulances"],
    shareText: "Nigeria's spy agency (NIA) is spending ₦31.1B on hospitals - 46x more than the Health Ministry! #Decide9ja",
  },
  {
    id: "nass-cost",
    tag: "Audit",
    tagColor: "bg-yellow-500/20 text-yellow-400",
    title: "Cost per Legislator",
    stat1: { label: "Per Lawmaker (469)", value: "₦735M" },
    highlight: "4,900 years min wage",
    highlightColor: "bg-yellow-500 text-black",
    description: "Each Nigerian legislator costs ₦735 million per year. That's equivalent to 4,900 years of minimum wage.",
    impact: ["4 primary schools", "4 health centers", "147 boreholes"],
    shareText: "Each Nigerian lawmaker costs ₦735M/year - that's 4,900 YEARS of minimum wage! #Decide9ja",
  },
  {
    id: "police-meals",
    tag: "Anomaly",
    tagColor: "bg-orange-500/20 text-orange-400",
    title: "Police Academy Feeding Schools",
    stat1: { label: "Police Academy Wudil", value: "₦5.9B" },
    stat2: { label: "Budget line", value: "School Meals" },
    highlight: "Wrong ministry",
    highlightColor: "bg-orange-500 text-white",
    description: "Nigeria Police Academy is budgeting ₦5.9 billion for school meal subsidies. This should be under Education.",
    impact: ["39 primary schools", "1,180 boreholes"],
    shareText: "Why is a Police Academy spending ₦5.9B on school meals? #Decide9ja",
  },
  {
    id: "nass-travel",
    tag: "Travel",
    tagColor: "bg-blue-500/20 text-blue-400",
    title: "NASS Travel Budget",
    stat1: { label: "NASS Travel", value: "₦22.49B" },
    stat2: { label: "Health Drugs", value: "₦42.2B" },
    highlight: "53% of drugs budget",
    highlightColor: "bg-blue-500 text-white",
    description: "The National Assembly's travel budget alone is more than half of what Health spends on drugs for 10 million Nigerians.",
    impact: ["150 primary schools", "4,498 boreholes"],
    shareText: "NASS travel budget (₦22.49B) is 53% of what Health spends on drugs! #Decide9ja",
  },
  {
    id: "army-roads",
    tag: "Mandate",
    tagColor: "bg-purple-500/20 text-purple-400",
    title: "Army Building Roads",
    stat1: { label: "Nigerian Army", value: "₦3.72B" },
    stat2: { label: "Budget line", value: "Road Construction" },
    highlight: "Outside mandate",
    highlightColor: "bg-purple-500 text-white",
    description: "The Nigerian Army has ₦3.72 billion for road construction. This should be under the Federal Ministry of Works.",
    impact: ["24 km paved roads", "744 boreholes"],
    shareText: "Why is the Army building roads? ₦3.72B outside their mandate! #Decide9ja",
  },
  {
    id: "total-anomalies",
    tag: "Summary",
    tagColor: "bg-[#25D366]/20 text-[#25D366]",
    title: "Total Suspicious Spending",
    stat1: { label: "Cross-MDA Anomalies", value: "₦86B" },
    stat2: { label: "Red Flags Found", value: "177" },
    highlight: "₦86 billion flagged",
    highlightColor: "bg-[#25D366] text-black",
    description: "Our analysis found 177 red flags totaling ₦86 billion in suspicious cross-MDA spending in the 2026 budget.",
    impact: ["573 schools", "17,200 boreholes", "1,720 ambulances"],
    shareText: "We found ₦86 BILLION in suspicious spending across 177 red flags! #Decide9ja",
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
        showToast("Shared!", "success");
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
    <section>
      {/* Toast */}
      {toast.show && (
        <div
          className="fixed bottom-24 left-4 right-4 md:left-auto md:right-6 md:w-72 z-[60]
            bg-gray-900 border border-gray-700 p-3 rounded-lg flex items-center gap-3 shadow-xl"
          role="alert"
        >
          {toast.type === "loading" && <Loader2 className="w-4 h-4 animate-spin text-[#25D366]" />}
          {toast.type === "success" && <span className="text-[#25D366]">✓</span>}
          {toast.type === "error" && <span className="text-red-500">✗</span>}
          <span className="text-sm">{toast.message}</span>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Budget Discoveries</h2>
        <span className="text-xs text-gray-500">{discoveries.length} findings</span>
      </div>

      {/* Grid - 2 columns on desktop, 1 on mobile */}
      <div className="grid gap-4 md:grid-cols-2">
        {discoveries.map((discovery) => {
          const isLoading = loadingStates[discovery.id];

          return (
            <article
              key={discovery.id}
              className="bg-gray-900/30 border border-gray-800 rounded-xl overflow-hidden
                hover:border-gray-700 transition-all hover:shadow-lg group"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 pb-0">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${discovery.tagColor}`}>
                  {discovery.tag}
                </span>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleShare(discovery)}
                    disabled={!!isLoading}
                    className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
                    aria-label="Share"
                  >
                    {isLoading === "share" ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Share2 size={16} className="text-gray-400" />
                    )}
                  </button>
                  <button
                    onClick={() => handleGenerateCard(discovery)}
                    disabled={!!isLoading}
                    className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
                    aria-label="Download card"
                  >
                    {isLoading === "download" ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Download size={16} className="text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-semibold text-lg mb-3">{discovery.title}</h3>

                {/* Stats Row */}
                <div className="flex gap-4 mb-3">
                  {discovery.stat1 && (
                    <div>
                      <div className="text-2xl font-bold text-white">{discovery.stat1.value}</div>
                      <div className="text-xs text-gray-500">{discovery.stat1.label}</div>
                    </div>
                  )}
                  {discovery.stat2 && (
                    <div>
                      <div className="text-2xl font-bold text-gray-400">{discovery.stat2.value}</div>
                      <div className="text-xs text-gray-500">{discovery.stat2.label}</div>
                    </div>
                  )}
                </div>

                {/* Highlight Badge */}
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mb-3 ${discovery.highlightColor}`}>
                  {discovery.highlight}
                </div>

                {/* Description */}
                <p className="text-sm text-gray-400 leading-relaxed mb-4">
                  {discovery.description}
                </p>

                {/* Impact */}
                {discovery.impact && (
                  <div className="pt-3 border-t border-gray-800">
                    <div className="text-xs text-gray-500 mb-2">Could build instead:</div>
                    <div className="flex flex-wrap gap-2">
                      {discovery.impact.map((item, i) => (
                        <span key={i} className="text-xs bg-gray-800/50 px-2 py-1 rounded text-gray-300">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Footer */}
              <div className="flex border-t border-gray-800">
                <button
                  onClick={() => handleShare(discovery)}
                  disabled={!!isLoading}
                  className="flex-1 py-3 text-sm flex items-center justify-center gap-2
                    text-gray-400 hover:text-white hover:bg-gray-800/50 transition-colors"
                >
                  {isLoading === "share" ? <Loader2 size={14} className="animate-spin" /> : <Share2 size={14} />}
                  Share
                </button>
                <div className="w-px bg-gray-800" />
                <button
                  onClick={() => handleGenerateCard(discovery)}
                  disabled={!!isLoading}
                  className="flex-1 py-3 text-sm flex items-center justify-center gap-2
                    text-gray-400 hover:text-white hover:bg-gray-800/50 transition-colors"
                >
                  {isLoading === "download" ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                  Download
                </button>
              </div>
            </article>
          );
        })}
      </div>

      {/* View All Link */}
      <div className="mt-6 text-center">
        <button className="inline-flex items-center gap-2 text-sm text-[#25D366] hover:text-[#20bd5a] transition-colors">
          View all 177 anomalies
          <ArrowRight size={16} />
        </button>
      </div>
    </section>
  );
}
