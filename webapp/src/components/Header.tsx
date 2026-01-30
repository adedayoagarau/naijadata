"use client";

import { useState, useEffect } from "react";

export function Header() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      setTime(`${hours}:${minutes}`);
    };

    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="p-4 border-b border-gray-800 bg-[#050505] sticky top-0 z-40">
      <div className="flex justify-between items-center">
        <div className="flex items-baseline gap-1">
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Decide<span className="text-[#25D366]">9ja</span>
          </h1>
          <span className="text-[10px] text-gray-600 hidden md:inline">Budget Transparency</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-600 hidden sm:inline">Federal Republic of Nigeria</span>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="w-2 h-2 bg-[#25D366] rounded-full animate-pulse" />
            <span className="font-mono">{time || "--:--"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
