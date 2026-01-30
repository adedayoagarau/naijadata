"use client";

import { useState } from "react";
import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { ChatInput } from "@/components/ChatInput";
import { DiscoveryFeed } from "@/components/DiscoveryFeed";
import { ChatButton } from "@/components/ChatButton";
import { ChatModal } from "@/components/ChatModal";
import { BarChart3, FileText, AlertTriangle } from "lucide-react";

export default function Home() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [initialQuestion, setInitialQuestion] = useState("");

  const handleAskQuestion = (question: string) => {
    setInitialQuestion(question);
    setIsChatOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Header />

      {/* Desktop Layout */}
      <div className="max-w-7xl mx-auto">
        {/* Hero Section */}
        <Hero />

        {/* Search Section */}
        <section className="px-4 lg:px-8 py-6 border-b border-gray-800">
          <div className="max-w-2xl">
            <ChatInput
              onSubmit={handleAskQuestion}
              placeholder="Ask anything about the 2026 budget..."
            />
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="text-xs text-gray-500">Popular:</span>
              {[
                "Why is NIA building hospitals?",
                "Compare NASS to Health spending",
                "Education budget breakdown",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleAskQuestion(suggestion)}
                  className="text-xs text-gray-400 hover:text-white bg-gray-900 hover:bg-gray-800
                    px-3 py-1.5 rounded-full transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Main Content - Responsive Grid */}
        <div className="lg:grid lg:grid-cols-4 lg:gap-6 px-4 lg:px-8 py-6">
          {/* Sidebar - Desktop Only */}
          <aside className="hidden lg:block lg:col-span-1">
            <div className="sticky top-20 space-y-4">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">Quick Stats</h3>

              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <BarChart3 className="w-5 h-5 text-[#25D366]" />
                  <span className="text-sm text-gray-400">Total Budget</span>
                </div>
                <div className="text-2xl font-bold">₦28.7T</div>
                <div className="text-xs text-gray-500 mt-1">2026 Federal Budget</div>
              </div>

              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <span className="text-sm text-gray-400">Red Flags</span>
                </div>
                <div className="text-2xl font-bold text-red-500">177</div>
                <div className="text-xs text-gray-500 mt-1">Anomalies detected</div>
              </div>

              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="w-5 h-5 text-blue-500" />
                  <span className="text-sm text-gray-400">Suspicious</span>
                </div>
                <div className="text-2xl font-bold">₦86B</div>
                <div className="text-xs text-gray-500 mt-1">In questionable spending</div>
              </div>

              <div className="mt-6 p-4 bg-[#25D366]/10 border border-[#25D366]/30 rounded-lg">
                <h4 className="text-sm font-semibold text-[#25D366] mb-2">About This Data</h4>
                <p className="text-xs text-gray-400 leading-relaxed">
                  Analysis of the 2026 Federal Appropriation Bill (2,790 pages).
                  Data extracted and verified against official government sources.
                </p>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-3">
            {/* Mobile Stats - Only on mobile */}
            <div className="lg:hidden grid grid-cols-3 gap-3 mb-6">
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-3 text-center">
                <div className="text-lg font-bold">₦28.7T</div>
                <div className="text-[10px] text-gray-500">Budget</div>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-red-500">177</div>
                <div className="text-[10px] text-gray-500">Red Flags</div>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-3 text-center">
                <div className="text-lg font-bold">₦86B</div>
                <div className="text-[10px] text-gray-500">Suspicious</div>
              </div>
            </div>

            <DiscoveryFeed />
          </main>
        </div>

        {/* Footer */}
        <footer className="px-4 lg:px-8 py-6 border-t border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <p className="text-sm text-gray-400">
                Built for budget transparency
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Data source: 2026 Federal Appropriation Bill
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="w-2 h-2 bg-[#25D366] rounded-full" />
              Live analysis
            </div>
          </div>
        </footer>
      </div>

      {/* Chat FAB and Modal */}
      <ChatButton onClick={() => setIsChatOpen(true)} />
      <ChatModal
        isOpen={isChatOpen}
        onClose={() => {
          setIsChatOpen(false);
          setInitialQuestion("");
        }}
        initialQuestion={initialQuestion}
      />
    </div>
  );
}
