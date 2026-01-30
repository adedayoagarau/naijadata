"use client";

import { useState, useEffect } from "react";

export function Header() {
  const [time, setTime] = useState("00:00");

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
    <header className="p-4 border-b-4 border-white bg-black sticky top-0 z-40">
      <div className="flex justify-between items-end">
        <h1 className="font-pixel text-5xl md:text-7xl leading-[0.7] tracking-tighter text-white">
          DECIDE<br />
          <span className="text-[#25D366]">9JA</span>
        </h1>
        <div className="flex flex-col items-end">
          <span className="font-mono text-xs mb-1">BUDGET_OS_V1.0</span>
          <div className="w-16 h-8 border border-white flex items-center justify-center bg-white text-black font-bold font-mono">
            {time}
          </div>
        </div>
      </div>
      <div className="flex justify-between mt-2 font-mono text-[10px] uppercase tracking-widest">
        <span>Fed. Republic of Nigeria</span>
        <span>Transparency_Protocol</span>
      </div>
    </header>
  );
}
