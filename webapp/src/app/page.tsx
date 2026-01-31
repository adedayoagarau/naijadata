"use client";

import { useState, useEffect, useRef, useCallback } from "react";

// Nigerian Budget Findings - will be fetched from API
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
}

const Texture = () => (
  <div
    className="fixed inset-0 opacity-[0.08] pointer-events-none z-[9999]"
    style={{
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
    }}
  />
);

const Header = ({ findingsCount }: { findingsCount: number }) => (
  <header className="bg-c-black text-gray-500 px-4 md:px-8 py-4 md:py-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-2 font-display text-xs tracking-wide border-b border-c-border flex-shrink-0">
    <h1 className="text-white font-normal text-xs tracking-[0.2em] uppercase">
      Decide9ja // Budget Transparency DB
    </h1>
    <nav className="flex gap-4 md:gap-16 text-[10px] md:text-xs">
      <a href="#" className="text-gray-500 hover:text-white transition-colors">
        ARCHIVE ({findingsCount})
      </a>
      <a href="#" className="text-gray-500 hover:text-white transition-colors">
        ALERTS
      </a>
      <a href="#" className="text-gray-500 hover:text-white transition-colors">
        ABOUT
      </a>
      <span className="text-gray-600">01.30.26</span>
    </nav>
  </header>
);

type BlockColor = "red" | "blue" | "green" | "yellow" | "beige" | "brown";

interface BudgetBlockProps {
  label: string;
  value: string;
  meta: string | { left: string; right: string };
  bgColor: BlockColor;
  span?: number;
  row?: number;
  hasAlert?: boolean;
  onClick?: () => void;
}

const BudgetBlock = ({
  label,
  value,
  meta,
  bgColor,
  span = 1,
  row = 1,
  hasAlert,
  onClick,
}: BudgetBlockProps) => {
  const colorClasses: Record<BlockColor, string> = {
    red: "bg-c-red text-black",
    blue: "bg-c-blue text-white",
    green: "bg-c-green text-black",
    yellow: "bg-c-yellow text-black",
    beige: "bg-c-beige text-black",
    brown: "bg-c-brown text-black",
  };

  const spanClass = span === 2 ? "col-span-2" : span === 3 ? "col-span-3" : "";
  const rowClass = row === 2 ? "row-span-2" : "";

  return (
    <div
      onClick={onClick}
      className={`${colorClasses[bgColor]} ${spanClass} ${rowClass} p-3 md:p-5 relative flex flex-col justify-between transition-all duration-200 cursor-pointer hover:brightness-110 overflow-hidden min-h-[120px] md:min-h-[140px]`}
    >
      <span className="text-[10px] md:text-xs uppercase tracking-wider opacity-70 mb-2">
        {label}
      </span>
      <div
        className="text-lg md:text-2xl lg:text-3xl font-medium tracking-tight leading-tight break-words"
        dangerouslySetInnerHTML={{ __html: value }}
      />

      {hasAlert && (
        <div className="absolute top-2 right-2 md:top-3 md:right-3 border border-current rounded-full w-6 h-6 md:w-8 md:h-8 flex items-center justify-center text-[10px] md:text-xs -rotate-12">
          !
        </div>
      )}

      <div
        className={`mt-auto pt-3 md:pt-4 font-mono text-[10px] md:text-xs flex justify-between items-end border-t ${
          bgColor === "blue"
            ? "border-white/20"
            : "border-black/10"
        }`}
      >
        {typeof meta === "string" || !meta ? (
          <span>{meta || ""}</span>
        ) : (
          <>
            <span>{meta.left}</span>
            <span>{meta.right}</span>
          </>
        )}
      </div>
    </div>
  );
};

interface ChatMessage {
  type: "system" | "user";
  content: string;
}

const AnalystPanel = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      type: "system",
      content:
        "&gt; Connected to Decide9ja Database v2.4<br />&gt; Analyzing Nigerian federal &amp; state budgets...<br />&gt; Ready for query.",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{role: string; content: string}>>([]);
  const historyRef = useRef<HTMLDivElement>(null);

  // Suggested prompts for users
  const suggestedPrompts = [
    "What is the NIA hospital scandal?",
    "Compare NASS travel budget to health spending",
    "Show me critical findings over ₦10B",
    "What are the highest risk MDAs?",
  ];

  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (customMessage?: string) => {
    const messageToSend = customMessage || inputValue;
    if (!messageToSend.trim() || isLoading) return;

    setMessages((prev) => [...prev, { type: "user", content: messageToSend }]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: messageToSend,
          history: chatHistory,
          useTools: true,
        }),
      });

      const data = await response.json();

      // Update chat history
      setChatHistory(prev => [
        ...prev,
        { role: "user", content: messageToSend },
        { role: "assistant", content: data.response || data.error || "No response" }
      ]);

      // Format response for display (convert markdown-like to HTML)
      let formattedResponse = (data.response || data.error || "No response")
        .replace(/\n/g, "<br />")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/₦/g, "<span style='color: var(--c-green);'>₦</span>");

      // Add tools indicator if tools were used
      if (data.toolsUsed) {
        formattedResponse = `<span style="color: var(--c-blue); font-size: 10px;">[QUERIED DATABASE]</span><br /><br />` + formattedResponse;
      }

      setMessages((prev) => [
        ...prev,
        {
          type: "system",
          content: formattedResponse,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "system",
          content: "&gt; <span style='color: var(--c-red);'>ERROR:</span> Failed to connect to analyst. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside className="bg-c-beige flex flex-col border-l border-c-border h-full">
      <div className="p-4 md:p-5 border-b border-c-border bg-c-yellow flex justify-between items-center">
        <span className="text-base md:text-lg font-medium tracking-tight">
          AI DATA ANALYST
        </span>
        <div className="flex items-center gap-2">
          {isLoading && <span className="text-xs font-mono">QUERYING...</span>}
          <div className={`w-2.5 h-2.5 ${isLoading ? 'bg-c-yellow' : 'bg-c-green'} rounded-full border border-black ${isLoading ? 'animate-pulse' : ''}`} />
        </div>
      </div>

      <div
        ref={historyRef}
        className="flex-grow p-4 md:p-6 overflow-y-auto flex flex-col gap-4 md:gap-6"
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`text-sm leading-relaxed max-w-[90%] ${
              msg.type === "user"
                ? "self-end bg-c-black text-white px-3 py-2 md:px-4 md:py-3 rounded-sm font-display"
                : "self-start font-mono text-c-black"
            }`}
            dangerouslySetInnerHTML={{ __html: msg.content }}
          />
        ))}
        {isLoading && (
          <div className="self-start font-mono text-c-black animate-pulse">
            &gt; Analyzing budget data...
          </div>
        )}

        {/* Suggested prompts - show only at start */}
        {messages.length <= 1 && !isLoading && (
          <div className="mt-2">
            <span className="text-xs text-gray-500 font-mono block mb-2">&gt; TRY ASKING:</span>
            <div className="flex flex-wrap gap-2">
              {suggestedPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(prompt)}
                  className="text-xs bg-white/50 border border-c-border px-2 py-1 rounded hover:bg-white transition-colors text-left"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-c-border bg-white flex">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about budget anomalies..."
          className="flex-grow border-none p-4 md:p-6 font-display text-sm md:text-base bg-transparent outline-none text-c-black placeholder:text-gray-400"
        />
        <button
          onClick={() => handleSend()}
          disabled={isLoading}
          className="bg-c-red text-black border-l border-c-border px-4 md:px-6 font-mono font-bold cursor-pointer uppercase transition-colors hover:brightness-90 disabled:opacity-50 text-sm"
        >
          Run
        </button>
      </div>
    </aside>
  );
};

// Format amount in Naira
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

// Map severity to color
const severityToColor = (severity: string): BlockColor => {
  switch (severity) {
    case "CRITICAL":
      return "red";
    case "HIGH":
      return "blue";
    case "MEDIUM":
      return "yellow";
    default:
      return "beige";
  }
};

// Filter component
const FindingsFilter = ({
  onFilterChange,
  findings,
}: {
  onFilterChange: (filtered: Finding[]) => void;
  findings: Finding[];
}) => {
  const [severity, setSeverity] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [year, setYear] = useState<string>("ALL");

  const years = [...new Set(findings.map((f) => f.year))].sort((a, b) => b - a);

  useEffect(() => {
    let filtered = findings;

    if (severity !== "ALL") {
      filtered = filtered.filter((f) => f.severity === severity);
    }
    if (year !== "ALL") {
      filtered = filtered.filter((f) => f.year === parseInt(year));
    }
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (f) =>
          f.entity?.toLowerCase().includes(q) ||
          f.description?.toLowerCase().includes(q) ||
          f.type?.toLowerCase().includes(q)
      );
    }

    onFilterChange(filtered);
  }, [severity, search, year, findings, onFilterChange]);

  return (
    <div className="bg-c-black border-b border-c-border p-3 flex flex-wrap gap-2 items-center">
      <select
        value={severity}
        onChange={(e) => setSeverity(e.target.value)}
        className="bg-transparent border border-gray-600 text-white text-xs px-2 py-1 rounded"
      >
        <option value="ALL">All Severity</option>
        <option value="CRITICAL">Critical</option>
        <option value="HIGH">High</option>
        <option value="MEDIUM">Medium</option>
        <option value="LOW">Low</option>
      </select>
      <select
        value={year}
        onChange={(e) => setYear(e.target.value)}
        className="bg-transparent border border-gray-600 text-white text-xs px-2 py-1 rounded"
      >
        <option value="ALL">All Years</option>
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
      <input
        type="text"
        placeholder="Search entities..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="bg-transparent border border-gray-600 text-white text-xs px-2 py-1 rounded flex-1 min-w-[120px] placeholder:text-gray-500"
      />
      <span className="text-gray-500 text-xs font-mono ml-auto">
        {findings.length} TOTAL
      </span>
    </div>
  );
};

// Stats bar component
const StatsBar = ({ findings }: { findings: Finding[] }) => {
  const critical = findings.filter((f) => f.severity === "CRITICAL").length;
  const high = findings.filter((f) => f.severity === "HIGH").length;
  const totalAmount = findings.reduce((sum, f) => sum + (f.amount || 0), 0);

  return (
    <div className="bg-c-black border-b border-c-border px-4 py-2 flex gap-4 text-xs font-mono overflow-x-auto">
      <span className="text-white">
        <span className="text-gray-500">FLAGGED:</span> {formatAmount(totalAmount)}
      </span>
      <span className="text-[#D6453A]">
        <span className="text-gray-500">CRITICAL:</span> {critical}
      </span>
      <span className="text-[#164678]">
        <span className="text-gray-500">HIGH:</span> {high}
      </span>
      <span className="text-gray-400">
        <span className="text-gray-500">ITEMS:</span> {findings.length}
      </span>
    </div>
  );
};

export default function Home() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [filteredFindings, setFilteredFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  useEffect(() => {
    // Load findings from API or local data
    const loadFindings = async () => {
      try {
        const res = await fetch("/api/findings");
        if (res.ok) {
          const data = await res.json();
          setFindings(data.findings || []);
          setFilteredFindings(data.findings || []);
        }
      } catch (err) {
        console.error("Failed to load findings:", err);
        // Use demo data if API fails
        setFindings(DEMO_FINDINGS);
        setFilteredFindings(DEMO_FINDINGS);
      } finally {
        setLoading(false);
      }
    };
    loadFindings();
  }, []);

  // Callback for filter changes
  const handleFilterChange = useCallback((filtered: Finding[]) => {
    setFilteredFindings(filtered);
  }, []);

  const criticalFindings = findings.filter((f) => f.severity === "CRITICAL");
  const highFindings = findings.filter((f) => f.severity === "HIGH");
  const totalFlagged = findings.reduce((sum, f) => sum + (f.amount || 0), 0);

  return (
    <div
      className="min-h-screen"
      style={
        {
          "--c-red": "#D6453A",
          "--c-blue": "#164678",
          "--c-green": "#487A3A",
          "--c-yellow": "#EBC346",
          "--c-beige": "#D9D9CD",
          "--c-brown": "#9E7D45",
          "--c-black": "#050505",
          "--c-border": "#111111",
        } as React.CSSProperties
      }
    >
      <Texture />
      <div className="bg-c-beige text-c-black font-display overflow-x-hidden h-screen flex flex-col">
        <Header findingsCount={findings.length} />

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_380px] xl:grid-cols-[1fr_420px] overflow-hidden">
          {/* Main Content Area */}
          <div className="flex flex-col overflow-hidden border-r border-c-border">
            {/* Stats Bar */}
            <StatsBar findings={findings} />

            {/* Filter Bar */}
            <FindingsFilter findings={findings} onFilterChange={handleFilterChange} />

            {/* Budget Grid */}
            <main className="grid grid-cols-2 md:grid-cols-4 auto-rows-[minmax(120px,auto)] md:auto-rows-[minmax(140px,auto)] overflow-y-auto bg-c-black gap-[1.5px] flex-1">
            {/* Hero Block - Priority Investigation */}
            {criticalFindings.length > 0 && (
              <BudgetBlock
                label="Priority Investigation"
                value={criticalFindings[0]?.entity || "Federal Budget<br />2026"}
                meta={{
                  left: `${criticalFindings.length} CRITICAL`,
                  right: formatAmount(totalFlagged) + " FLAGGED",
                }}
                bgColor="red"
                span={2}
                row={2}
                onClick={() => setSelectedFinding(criticalFindings[0])}
              />
            )}

            {/* Dynamic blocks from filtered findings */}
            {filteredFindings.slice(0, 20).map((finding, idx) => {
              const colors: BlockColor[] = [
                "beige",
                "blue",
                "yellow",
                "green",
                "brown",
              ];
              const spans = [1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 3];

              return (
                <BudgetBlock
                  key={finding.id || idx}
                  label={finding.type?.replace(/_/g, " ") || "Finding"}
                  value={
                    finding.entity?.length > 30
                      ? finding.entity.substring(0, 30) + "..."
                      : finding.entity || "Unknown"
                  }
                  meta={
                    finding.amount
                      ? formatAmount(finding.amount)
                      : finding.severity
                  }
                  bgColor={severityToColor(finding.severity)}
                  span={spans[idx % spans.length]}
                  hasAlert={finding.severity === "CRITICAL"}
                  onClick={() => setSelectedFinding(finding)}
                />
              );
            })}

            {/* Summary blocks */}
            <BudgetBlock
              label="Total Anomalies"
              value={findings.length.toString()}
              meta={{ left: "ALL YEARS", right: "FEDERAL + STATES" }}
              bgColor="brown"
              span={2}
            />

            <BudgetBlock
              label="High Risk MDAs"
              value={
                highFindings.length > 0
                  ? highFindings[0]?.entity?.split(" ").slice(0, 3).join(" ") ||
                    "Various"
                  : "Under Review"
              }
              meta={`${highFindings.length} FLAGGED`}
              bgColor="blue"
            />

            <BudgetBlock
              label="Data Coverage"
              value="36 States<br />+ Federal"
              meta="2025-2026"
              bgColor="green"
            />

            {loading && (
              <BudgetBlock
                label="Status"
                value="Loading..."
                meta="PLEASE WAIT"
                bgColor="beige"
                span={2}
              />
            )}

            {/* No results message */}
            {!loading && filteredFindings.length === 0 && (
              <div className="col-span-full p-8 text-center text-gray-500">
                <p className="text-lg">No findings match your filters</p>
                <p className="text-sm mt-2">Try adjusting severity or search terms</p>
              </div>
            )}
          </main>
          </div>

          {/* AI Analyst Panel */}
          <AnalystPanel />
        </div>
      </div>

      {/* Finding Detail Modal */}
      {selectedFinding && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedFinding(null)}
        >
          <div
            className="bg-c-beige max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6 md:p-8"
            onClick={(e) => e.stopPropagation()}
            style={{ "--c-beige": "#D9D9CD" } as React.CSSProperties}
          >
            <div className="flex justify-between items-start mb-4">
              <span
                className={`px-3 py-1 text-xs font-mono uppercase ${
                  selectedFinding.severity === "CRITICAL"
                    ? "bg-[#D6453A] text-black"
                    : selectedFinding.severity === "HIGH"
                    ? "bg-[#164678] text-white"
                    : "bg-[#EBC346] text-black"
                }`}
              >
                {selectedFinding.severity}
              </span>
              <button
                onClick={() => setSelectedFinding(null)}
                className="text-2xl leading-none hover:opacity-70"
              >
                ×
              </button>
            </div>

            <h2 className="text-2xl md:text-3xl font-medium mb-2">
              {selectedFinding.entity}
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              {selectedFinding.type?.replace(/_/g, " ")} • {selectedFinding.year}
              {selectedFinding.state && ` • ${selectedFinding.state}`}
            </p>

            {selectedFinding.amount > 0 && (
              <div className="text-4xl font-bold mb-4">
                {formatAmount(selectedFinding.amount)}
              </div>
            )}

            <p className="text-base leading-relaxed mb-6">
              {selectedFinding.description}
            </p>

            {selectedFinding.recommendation && (
              <div className="bg-[#EBC346]/30 p-4 border-l-4 border-[#EBC346] mb-6">
                <h4 className="font-bold text-sm mb-2">RECOMMENDATION</h4>
                <p className="text-sm">{selectedFinding.recommendation}</p>
              </div>
            )}

            {/* Share Buttons */}
            <div className="flex flex-col gap-3 pt-4 border-t border-gray-300">
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    const text = `🚨 ${selectedFinding.entity}: ${formatAmount(selectedFinding.amount)}\n\n${selectedFinding.description}\n\n#Decide9ja #BudgetTransparency`;
                    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
                    window.open(url, '_blank');
                  }}
                  className="flex-1 bg-c-black text-white py-3 font-mono text-sm uppercase hover:bg-gray-800 transition-colors"
                >
                  Share on X
                </button>
                <button
                  onClick={() => {
                    const text = `🚨 *BUDGET ALERT*\n\n*${selectedFinding.entity}*\n${formatAmount(selectedFinding.amount)}\n\n${selectedFinding.description}\n\n_Source: Decide9ja Budget Transparency_\n#Decide9ja`;
                    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
                    window.open(url, '_blank');
                  }}
                  className="flex-1 bg-[#25D366] text-white py-3 font-mono text-sm uppercase hover:brightness-90 transition-colors"
                >
                  WhatsApp
                </button>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    const shareUrl = `${window.location.origin}/finding/${selectedFinding.id}`;
                    navigator.clipboard.writeText(shareUrl);
                    alert('Link copied!');
                  }}
                  className="flex-1 bg-white border border-c-border text-c-black py-3 font-mono text-sm uppercase hover:bg-gray-100 transition-colors"
                >
                  Copy Link
                </button>
                <a
                  href={`/finding/${selectedFinding.id}`}
                  target="_blank"
                  className="flex-1 bg-[#164678] text-white py-3 font-mono text-sm uppercase hover:brightness-90 transition-colors text-center"
                >
                  View Full Page
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Demo data for when API is unavailable
const DEMO_FINDINGS: Finding[] = [
  {
    id: "1",
    type: "MANDATE_VIOLATION",
    entity: "National Intelligence Agency",
    description: "Security agency allocated ₦5.2B for hospital construction - outside core mandate",
    amount: 5_200_000_000,
    severity: "CRITICAL",
    year: 2026,
  },
  {
    id: "2",
    type: "YOY_VARIANCE",
    entity: "National Assembly",
    description: "320% increase in travel allowances compared to 2025",
    amount: 12_400_000_000,
    severity: "HIGH",
    year: 2026,
  },
  {
    id: "3",
    type: "ROUND_NUMBER",
    entity: "Ministry of Works",
    description: "Exact ₦10B allocation suggests estimation rather than actual costing",
    amount: 10_000_000_000,
    severity: "MEDIUM",
    year: 2026,
  },
  {
    id: "4",
    type: "CROSS_MDA_OUTLIER",
    entity: "Office of the NSA",
    description: "Spending 8.5x median for budget code 2305 (Security Equipment)",
    amount: 45_000_000_000,
    severity: "CRITICAL",
    year: 2026,
  },
  {
    id: "5",
    type: "BENFORD_VIOLATION",
    entity: "Ministry of Education",
    description: "First digit distribution deviates significantly from Benford's Law",
    amount: 1_800_000_000_000,
    severity: "HIGH",
    year: 2026,
  },
  {
    id: "6",
    type: "PADDING_INDICATOR",
    entity: "Federal Road Maintenance Agency",
    description: "Vehicle costs 450% above market benchmark",
    amount: 8_500_000_000,
    severity: "HIGH",
    year: 2026,
  },
  {
    id: "7",
    type: "STATE_COMPARISON",
    entity: "Lagos State",
    description: "Budget 3.2x higher than median state budget",
    amount: 4_445_000_000_000,
    severity: "MEDIUM",
    year: 2026,
    state: "Lagos",
  },
  {
    id: "8",
    type: "EDUCATION_ALLOCATION",
    entity: "Akwa Ibom State",
    description: "Only 2.27% allocated to education - lowest in nation",
    amount: 31_600_000_000,
    severity: "HIGH",
    year: 2026,
    state: "Akwa Ibom",
  },
];
