"use client";

import { useState } from "react";
import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { ChatInput } from "@/components/ChatInput";
import { DiscoveryFeed } from "@/components/DiscoveryFeed";
import { ChatButton } from "@/components/ChatButton";
import { ChatModal } from "@/components/ChatModal";

export default function Home() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [initialQuestion, setInitialQuestion] = useState("");

  const handleAskQuestion = (question: string) => {
    setInitialQuestion(question);
    setIsChatOpen(true);
  };

  return (
    <div className="min-h-screen flex flex-col relative pb-20 bg-[#050505]">
      <Header />

      <main className="flex-1 flex flex-col">
        {/* Hero / Onboarding */}
        <Hero />

        {/* Search Input */}
        <section className="p-4 border-b border-gray-800">
          <ChatInput
            onSubmit={handleAskQuestion}
            placeholder="Ask anything about the budget..."
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="text-xs text-gray-600">Try:</span>
            {[
              "Why is NIA building hospitals?",
              "How much do legislators earn?",
              "Show me education spending",
            ].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleAskQuestion(suggestion)}
                className="text-xs text-gray-500 hover:text-white border border-gray-800
                  px-2 py-1 hover:border-gray-600 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </section>

        {/* Main Content */}
        <DiscoveryFeed />

        {/* Footer */}
        <footer className="p-4 border-t border-gray-800 mt-auto">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <p className="text-xs text-gray-600">
                Data source: 2026 Federal Appropriation Bill
              </p>
              <p className="text-xs text-gray-700 mt-1">
                Built for budget transparency by Nigerians, for Nigerians
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-[#25D366] rounded-full animate-pulse" />
              <span className="text-xs text-gray-500">Live analysis</span>
            </div>
          </div>
        </footer>
      </main>

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
