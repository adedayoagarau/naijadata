"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

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
  CRITICAL: { bg: "#D6453A", text: "#000000" },
  HIGH: { bg: "#164678", text: "#FFFFFF" },
  MEDIUM: { bg: "#EBC346", text: "#000000" },
  LOW: { bg: "#D9D9CD", text: "#000000" },
};

type CardTemplate = "alert" | "stat" | "comparison";
type CardStyle = "dark" | "light";

export default function CardGeneratorPage() {
  const params = useParams();
  const id = params.id as string;

  const [finding, setFinding] = useState<Finding | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [template, setTemplate] = useState<CardTemplate>("alert");
  const [style, setStyle] = useState<CardStyle>("dark");
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadFinding = async () => {
      try {
        const res = await fetch(`/api/findings/${id}`);
        if (res.ok) {
          const data = await res.json();
          setFinding(data.finding);
        }
      } catch (err) {
        console.error("Failed to load finding:", err);
      } finally {
        setLoading(false);
      }
    };
    if (id) loadFinding();
  }, [id]);

  const generateImage = async () => {
    if (!finding) return;

    setGenerating(true);
    try {
      const response = await fetch("/api/generate-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          finding,
          style: template,
        }),
      });

      const data = await response.json();
      if (data.imageSpec) {
        // For now, we'll use the card preview as the generated image
        // In production, this would return an actual generated image URL
        setGeneratedImage(data.imageSpec.description);
      }
    } catch (err) {
      console.error("Failed to generate image:", err);
    } finally {
      setGenerating(false);
    }
  };

  const downloadCard = async () => {
    if (!cardRef.current) return;

    try {
      // Dynamic import html-to-image
      const { toPng } = await import("html-to-image");
      const dataUrl = await toPng(cardRef.current, {
        quality: 1,
        pixelRatio: 2,
      });

      const link = document.createElement("a");
      link.download = `decide9ja-${finding?.id || "card"}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error("Failed to download card:", err);
      alert("Failed to download card. Please try again.");
    }
  };

  const shareToWhatsApp = () => {
    if (!finding) return;
    const text = `🚨 *BUDGET ALERT*\n\n*${finding.entity}*\n${formatAmount(finding.amount)}\n\n${finding.description}\n\n_Source: Decide9ja Budget Transparency_\n#Decide9ja`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
  };

  const shareToTwitter = () => {
    if (!finding) return;
    const text = `🚨 ${finding.entity}: ${formatAmount(finding.amount)}\n\n${finding.description}\n\n#Decide9ja #BudgetTransparency`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, "_blank");
  };

  const today = new Date();
  const dateStr = `${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}.${String(today.getFullYear()).slice(-2)}`;

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!finding) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-500 mb-4">Finding not found</div>
          <Link href="/" className="text-[#487A3A] hover:underline">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const colors = severityColors[finding.severity];

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

      {/* Page Title */}
      <div className="bg-[#487A3A] px-4 md:px-8 py-6">
        <h1 className="text-2xl md:text-4xl font-bold text-white">GENERATE CARD</h1>
        <p className="text-white/70 mt-1">Create a shareable image for this finding</p>
      </div>

      <div className="px-4 md:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl">
          {/* Card Preview */}
          <div>
            <h2 className="text-white font-bold mb-4">PREVIEW</h2>
            <div
              ref={cardRef}
              className={`aspect-square max-w-md mx-auto ${style === "dark" ? "bg-[#050505]" : "bg-[#D9D9CD]"} p-6 flex flex-col`}
            >
              {template === "alert" && (
                <>
                  {/* Alert Template */}
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-2xl">🚨</span>
                    <span
                      className="px-2 py-1 text-xs font-mono uppercase"
                      style={{ backgroundColor: colors.bg, color: colors.text }}
                    >
                      {finding.severity}
                    </span>
                  </div>

                  <div className="flex-1 flex flex-col justify-center">
                    <h3
                      className={`text-xl font-bold mb-2 ${style === "dark" ? "text-white" : "text-black"}`}
                    >
                      {finding.entity}
                    </h3>
                    <div className="text-4xl font-bold text-[#D6453A] mb-4">
                      {formatAmount(finding.amount)}
                    </div>
                    <p
                      className={`text-sm leading-relaxed ${style === "dark" ? "text-gray-400" : "text-gray-600"}`}
                    >
                      {finding.description}
                    </p>
                  </div>

                  <div
                    className={`border-t pt-4 mt-4 flex justify-between items-center ${style === "dark" ? "border-gray-800" : "border-gray-400"}`}
                  >
                    <span
                      className={`text-xs font-mono ${style === "dark" ? "text-gray-500" : "text-gray-600"}`}
                    >
                      {finding.year} • {finding.type?.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs font-bold text-[#487A3A]">#Decide9ja</span>
                  </div>
                </>
              )}

              {template === "stat" && (
                <>
                  {/* Single Stat Template */}
                  <div className="flex-1 flex flex-col items-center justify-center text-center">
                    <span
                      className={`text-sm uppercase tracking-wider mb-4 ${style === "dark" ? "text-gray-500" : "text-gray-600"}`}
                    >
                      {finding.type?.replace(/_/g, " ")}
                    </span>
                    <div className="text-6xl font-bold text-[#D6453A] mb-4">
                      {formatAmount(finding.amount)}
                    </div>
                    <h3
                      className={`text-lg font-medium ${style === "dark" ? "text-white" : "text-black"}`}
                    >
                      {finding.entity}
                    </h3>
                  </div>

                  <div
                    className={`border-t pt-4 mt-4 text-center ${style === "dark" ? "border-gray-800" : "border-gray-400"}`}
                  >
                    <span className="text-xs font-bold text-[#487A3A]">
                      Decide9ja • Budget Transparency
                    </span>
                  </div>
                </>
              )}

              {template === "comparison" && (
                <>
                  {/* Comparison Template - placeholder for now */}
                  <div className="flex-1 flex flex-col justify-center">
                    <div className="text-center mb-6">
                      <span
                        className={`text-sm uppercase tracking-wider ${style === "dark" ? "text-gray-500" : "text-gray-600"}`}
                      >
                        Budget Finding
                      </span>
                    </div>

                    <div className="space-y-4">
                      <div
                        className={`p-4 ${style === "dark" ? "bg-[#111]" : "bg-white"}`}
                      >
                        <span
                          className={`text-xs ${style === "dark" ? "text-gray-500" : "text-gray-600"}`}
                        >
                          {finding.entity}
                        </span>
                        <div className="text-3xl font-bold text-[#D6453A]">
                          {formatAmount(finding.amount)}
                        </div>
                      </div>

                      <div className="text-center">
                        <span
                          className={`text-xs px-3 py-1 ${style === "dark" ? "bg-gray-800 text-gray-400" : "bg-gray-200 text-gray-600"}`}
                        >
                          FLAGGED: {finding.severity}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div
                    className={`border-t pt-4 mt-4 text-center ${style === "dark" ? "border-gray-800" : "border-gray-400"}`}
                  >
                    <span className="text-xs font-bold text-[#487A3A]">#Decide9ja</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Controls */}
          <div>
            <h2 className="text-white font-bold mb-4">OPTIONS</h2>

            {/* Template Selection */}
            <div className="mb-6">
              <label className="text-gray-500 text-xs block mb-2">TEMPLATE</label>
              <div className="flex gap-2">
                {(["alert", "stat", "comparison"] as CardTemplate[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTemplate(t)}
                    className={`px-4 py-2 text-sm capitalize ${template === t
                        ? "bg-white text-black"
                        : "bg-[#111] text-gray-400 hover:text-white"
                      } transition-colors`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* Style Selection */}
            <div className="mb-6">
              <label className="text-gray-500 text-xs block mb-2">STYLE</label>
              <div className="flex gap-2">
                {(["dark", "light"] as CardStyle[]).map((s) => (
                  <button
                    key={s}
                    onClick={() => setStyle(s)}
                    className={`px-4 py-2 text-sm capitalize ${style === s
                        ? "bg-white text-black"
                        : "bg-[#111] text-gray-400 hover:text-white"
                      } transition-colors`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* AI Generate Button */}
            <div className="mb-6">
              <label className="text-gray-500 text-xs block mb-2">AI IMAGE (BETA)</label>
              <button
                onClick={generateImage}
                disabled={generating}
                className="w-full bg-[#164678] text-white py-3 font-mono text-sm uppercase hover:brightness-90 transition-colors disabled:opacity-50"
              >
                {generating ? "Generating..." : "Generate AI Image"}
              </button>
              {generatedImage && (
                <p className="text-xs text-gray-500 mt-2">{generatedImage}</p>
              )}
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={downloadCard}
                className="w-full bg-[#487A3A] text-white py-3 font-mono text-sm uppercase hover:brightness-90 transition-colors"
              >
                Download Image
              </button>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={shareToTwitter}
                  className="bg-c-black border border-gray-600 text-white py-3 font-mono text-sm uppercase hover:bg-[#111] transition-colors"
                >
                  Share on X
                </button>
                <button
                  onClick={shareToWhatsApp}
                  className="bg-[#25D366] text-white py-3 font-mono text-sm uppercase hover:brightness-90 transition-colors"
                >
                  WhatsApp
                </button>
              </div>

              <Link
                href={`/finding/${finding.id}`}
                className="block text-center bg-[#111] border border-c-border text-gray-400 py-3 font-mono text-sm uppercase hover:text-white transition-colors"
              >
                View Finding Details
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
