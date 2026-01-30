"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader2, X } from "lucide-react";

interface ToastProps {
  message: string;
  type: "success" | "error" | "loading";
  onClose: () => void;
}

export function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    if (type !== "loading") {
      const timer = setTimeout(onClose, 4000);
      return () => clearTimeout(timer);
    }
  }, [type, onClose]);

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-[#25D366]" />,
    error: <XCircle className="w-5 h-5 text-red-500" />,
    loading: <Loader2 className="w-5 h-5 text-white animate-spin" />,
  };

  const bgColors = {
    success: "bg-[#0a0a0a] border-[#25D366]",
    error: "bg-[#0a0a0a] border-red-500",
    loading: "bg-[#0a0a0a] border-gray-500",
  };

  return (
    <div
      className={`fixed bottom-24 left-4 right-4 md:left-auto md:right-4 md:w-80 z-[60]
        border ${bgColors[type]} p-4 flex items-center gap-3 shadow-lg animate-slide-up`}
      role="alert"
      aria-live="polite"
    >
      {icons[type]}
      <span className="flex-1 text-sm">{message}</span>
      {type !== "loading" && (
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-800 rounded"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// Toast container for managing multiple toasts
interface ToastItem {
  id: string;
  message: string;
  type: "success" | "error" | "loading";
}

interface ToastContextValue {
  showToast: (message: string, type: "success" | "error" | "loading") => string;
  hideToast: (id: string) => void;
  updateToast: (id: string, message: string, type: "success" | "error" | "loading") => void;
}

import { createContext, useContext, useCallback } from "react";

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback((message: string, type: "success" | "error" | "loading") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, message, type }]);
    return id;
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const updateToast = useCallback((id: string, message: string, type: "success" | "error" | "loading") => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, message, type } : t))
    );
  }, []);

  return (
    <ToastContext.Provider value={{ showToast, hideToast, updateToast }}>
      {children}
      <div className="fixed bottom-24 left-0 right-0 z-[60] flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto px-4">
            <Toast
              message={toast.message}
              type={toast.type}
              onClose={() => hideToast(toast.id)}
            />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
