"use client";

import { useState, useEffect, useRef } from "react";

interface Finding {
  id: string;
  type: string;
  entity: string;
  description: string;
  amount: number;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  year: number;
  state?: string;
}

interface FindingsSliderProps {
  findings: Finding[];
  onSelectFinding: (finding: Finding) => void;
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
  CRITICAL: { bg: "#D6453A", text: "#fff" },
  HIGH: { bg: "#164678", text: "#fff" },
  MEDIUM: { bg: "#EBC346", text: "#000" },
  LOW: { bg: "#D9D9CD", text: "#000" },
};

export default function FindingsSlider({ findings, onSelectFinding }: FindingsSliderProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const sliderRef = useRef<HTMLDivElement>(null);

  // Auto-advance every 5 seconds
  useEffect(() => {
    if (!isAutoPlaying || findings.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % findings.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [isAutoPlaying, findings.length]);

  const goTo = (index: number) => {
    setCurrentIndex(index);
    setIsAutoPlaying(false);
    // Resume auto-play after 10 seconds of inactivity
    setTimeout(() => setIsAutoPlaying(true), 10000);
  };

  const goNext = () => goTo((currentIndex + 1) % findings.length);
  const goPrev = () => goTo((currentIndex - 1 + findings.length) % findings.length);

  if (findings.length === 0) return null;

  const currentFinding = findings[currentIndex];
  const colors = severityColors[currentFinding?.severity] || severityColors.MEDIUM;

  return (
    <div className="relative">
      {/* Main Slide */}
      <div
        ref={sliderRef}
        className="relative overflow-hidden"
        style={{ backgroundColor: colors.bg }}
      >
        <div
          className="p-6 md:p-8 cursor-pointer transition-all duration-300"
          onClick={() => onSelectFinding(currentFinding)}
        >
          {/* Severity Badge */}
          <div className="flex items-center gap-2 mb-3">
            <span
              className="px-2 py-1 text-[10px] font-mono uppercase border"
              style={{ borderColor: colors.text, color: colors.text }}
            >
              {currentFinding?.severity}
            </span>
            <span className="text-xs opacity-70" style={{ color: colors.text }}>
              {currentFinding?.state || "Federal"} • {currentFinding?.year}
            </span>
          </div>

          {/* Entity Name */}
          <h3
            className="text-xl md:text-2xl font-bold mb-2 leading-tight"
            style={{ color: colors.text }}
          >
            {currentFinding?.entity || currentFinding?.type?.replace(/_/g, " ")}
          </h3>

          {/* Amount */}
          <div className="text-3xl md:text-4xl font-bold mb-3" style={{ color: colors.text }}>
            {formatAmount(currentFinding?.amount || 0)}
          </div>

          {/* Description */}
          <p
            className="text-sm opacity-80 line-clamp-2"
            style={{ color: colors.text }}
          >
            {currentFinding?.description}
          </p>

          {/* Type Label */}
          <div
            className="mt-4 text-xs font-mono opacity-60"
            style={{ color: colors.text }}
          >
            {currentFinding?.type?.replace(/_/g, " ")}
          </div>
        </div>

        {/* Navigation Arrows */}
        {findings.length > 1 && (
          <>
            <button
              onClick={(e) => { e.stopPropagation(); goPrev(); }}
              className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center bg-black/30 hover:bg-black/50 rounded-full transition-colors"
              style={{ color: colors.text }}
            >
              ‹
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); goNext(); }}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center bg-black/30 hover:bg-black/50 rounded-full transition-colors"
              style={{ color: colors.text }}
            >
              ›
            </button>
          </>
        )}
      </div>

      {/* Dots Indicator */}
      {findings.length > 1 && (
        <div className="flex justify-center gap-1.5 py-2 bg-[#111]">
          {findings.slice(0, 10).map((_, idx) => (
            <button
              key={idx}
              onClick={() => goTo(idx)}
              className={`w-2 h-2 rounded-full transition-colors ${
                idx === currentIndex ? "bg-white" : "bg-gray-600 hover:bg-gray-500"
              }`}
            />
          ))}
          {findings.length > 10 && (
            <span className="text-gray-500 text-xs ml-1">+{findings.length - 10}</span>
          )}
        </div>
      )}
    </div>
  );
}
