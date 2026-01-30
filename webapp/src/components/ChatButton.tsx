"use client";

import { MessageSquare } from "lucide-react";

interface ChatButtonProps {
  onClick: () => void;
}

export function ChatButton({ onClick }: ChatButtonProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={onClick}
        className="bg-white text-black w-14 h-14 border-2 border-black brut-shadow-green flex items-center justify-center hover:scale-95 transition-transform"
      >
        <MessageSquare size={24} />
      </button>
    </div>
  );
}
