"use client";

import { useState, useEffect, useRef } from "react";
import { Header } from "@/components/Header";
import { Marquee } from "@/components/Marquee";
import { QueryCard } from "@/components/QueryCard";
import { ChatInput } from "@/components/ChatInput";
import { TrendingLogs } from "@/components/TrendingLogs";
import { RedFlags } from "@/components/RedFlags";
import { ChatButton } from "@/components/ChatButton";
import { ChatModal } from "@/components/ChatModal";
import { DiscoveryFeed } from "@/components/DiscoveryFeed";

export default function Home() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [currentQuery, setCurrentQuery] = useState<{
    question: string;
    answer: string;
    amount: string;
    comparison: string;
  } | null>({
    question: 'NIA HOSPITAL SPEND',
    answer: 'NIA is spending 31.1 billion naira on hospital repairs. That is 46 TIMES MORE than the Health Ministry spends on the same line item.',
    amount: '₦31.1 BILLION',
    comparison: '46 TIMES MORE'
  });

  return (
    <div className="min-h-screen flex flex-col relative pb-20">
      {/* Scanline overlay */}
      <div className="scanline" />

      <Header />
      <Marquee />

      <main className="flex-1 flex flex-col">
        {/* Query Section */}
        <section className="p-4 border-b border-white">
          {currentQuery && (
            <QueryCard
              question={currentQuery.question}
              answer={currentQuery.answer}
              amount={currentQuery.amount}
              comparison={currentQuery.comparison}
            />
          )}
          <ChatInput
            onSubmit={(question) => {
              setIsChatOpen(true);
            }}
          />
        </section>

        <DiscoveryFeed />
        <TrendingLogs />
        <RedFlags />

        {/* System Status */}
        <div className="mx-4 mt-8 border border-white p-2 flex justify-between items-center opacity-50">
          <div className="flex flex-col gap-1">
            <div className="w-20 h-[2px] bg-white" />
            <div className="w-10 h-[2px] bg-white" />
            <div className="w-5 h-[2px] bg-white" />
          </div>
          <div className="text-[8px] font-mono text-right">
            SYSTEM_READY<br />
            DECIDE9JA_CORE
          </div>
        </div>
      </main>

      <ChatButton onClick={() => setIsChatOpen(true)} />
      <ChatModal isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
