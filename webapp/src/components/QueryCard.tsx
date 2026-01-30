"use client";

import { useState } from "react";
import { Download } from "lucide-react";

interface QueryCardProps {
  question: string;
  answer: string;
  amount: string;
  comparison: string;
}

export function QueryCard({ question, answer, amount, comparison }: QueryCardProps) {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateCard = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch("/api/card", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: question,
          amount: amount,
          description: answer,
          comparison: comparison,
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "decide9ja-card.png";
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Error generating card:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="brut-border p-0 bg-black mb-6 relative group">
      {/* Corner decorations */}
      <div className="absolute -top-1 -left-1 w-2 h-2 border-t border-l border-white" />
      <div className="absolute -top-1 -right-1 w-2 h-2 border-t border-r border-white" />
      <div className="absolute -bottom-1 -left-1 w-2 h-2 border-b border-l border-white" />
      <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r border-white" />

      {/* Query header */}
      <div className="flex border-b border-white">
        <div className="w-12 border-r border-white flex items-center justify-center bg-[#111]">
          <div className="w-2 h-2 bg-[#25D366] rounded-full" />
        </div>
        <div className="flex-1 p-2 font-mono text-xs text-gray-400">
          QUERY: &quot;{question}&quot;
        </div>
      </div>

      {/* Main content */}
      <div className="p-4 relative overflow-hidden">
        <div className="absolute top-4 right-4 text-[#25D366] text-[10px] border border-[#25D366] px-1 pulse-green">
          LIVE DATA
        </div>

        <h2 className="font-pixel text-3xl md:text-4xl mb-2 text-white">{amount}</h2>
        <p className="font-mono text-sm leading-tight text-gray-300 mb-4 uppercase">
          {answer.split(comparison)[0]}
          <span className="bg-white text-black px-1">{comparison}</span>
          {answer.split(comparison)[1]}
        </p>

        <div className="flex gap-2 text-[10px] font-mono mb-4 text-gray-500">
          <div className="flex-1 border-r border-gray-700">
            DATA_ID: <span className="text-white">FED_2026_BILL</span>
          </div>
          <div className="flex-1 text-right">
            IMPACT: <span className="text-red-500">CRITICAL</span>
          </div>
        </div>

        <button
          onClick={handleGenerateCard}
          disabled={isGenerating}
          className="w-full bg-[#25D366] text-black font-bold font-mono py-3 text-sm uppercase border border-white hover:bg-white transition-colors flex items-center justify-between px-4 brut-shadow disabled:opacity-50"
        >
          <span>{isGenerating ? "[ GENERATING... ]" : "[ GENERATE CARD ]"}</span>
          <Download size={16} />
        </button>
      </div>

      {/* Barcode */}
      <div className="h-6 w-full barcode opacity-80 mix-blend-screen" />
    </div>
  );
}
