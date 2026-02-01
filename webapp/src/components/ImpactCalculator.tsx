"use client";

import { useState } from "react";

// What Nigerian money can build
const IMPACT_BENCHMARKS = {
  primary_school: {
    cost: 150_000_000,
    label: "Primary Schools",
    description: "6 classrooms, 240 students each",
    icon: "🏫",
  },
  health_center: {
    cost: 150_000_000,
    label: "Health Centers",
    description: "Serves 10,000 people",
    icon: "🏥",
  },
  borehole: {
    cost: 5_000_000,
    label: "Boreholes",
    description: "Clean water for 500 people",
    icon: "💧",
  },
  ambulance: {
    cost: 50_000_000,
    label: "Ambulances",
    description: "Fully equipped emergency vehicle",
    icon: "🚑",
  },
  road_km: {
    cost: 150_000_000,
    label: "Km of Road",
    description: "Paved road construction",
    icon: "🛣️",
  },
  affordable_house: {
    cost: 15_000_000,
    label: "Houses",
    description: "Affordable 2-bedroom home",
    icon: "🏠",
  },
  child_vaccination: {
    cost: 15_000,
    label: "Child Vaccinations",
    description: "Full immunization program",
    icon: "💉",
  },
  malaria_treatment: {
    cost: 5_000,
    label: "Malaria Treatments",
    description: "Full treatment course",
    icon: "💊",
  },
  yearly_minimum_wage: {
    cost: 840_000,
    label: "Years of Min. Wage",
    description: "₦70,000/month for a worker",
    icon: "👷",
  },
  university_scholarship: {
    cost: 500_000,
    label: "Scholarships",
    description: "1-year university scholarship",
    icon: "🎓",
  },
};

type BenchmarkKey = keyof typeof IMPACT_BENCHMARKS;

interface ImpactResult {
  key: BenchmarkKey;
  count: number;
  label: string;
  description: string;
  icon: string;
  total_value: number;
}

function calculateImpact(amount: number): ImpactResult[] {
  return Object.entries(IMPACT_BENCHMARKS)
    .map(([key, { cost, label, description, icon }]) => ({
      key: key as BenchmarkKey,
      count: Math.floor(amount / cost),
      label,
      description,
      icon,
      total_value: Math.floor(amount / cost) * cost,
    }))
    .filter((item) => item.count > 0)
    .sort((a, b) => {
      // Prioritize meaningful counts (not too small, not too huge)
      const aScore = a.count > 10 && a.count < 10000 ? a.count : a.count / 1000;
      const bScore = b.count > 10 && b.count < 10000 ? b.count : b.count / 1000;
      return bScore - aScore;
    });
}

function formatAmount(amount: number): string {
  if (amount >= 1_000_000_000_000) {
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`;
  } else if (amount >= 1_000_000_000) {
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`;
  } else if (amount >= 1_000_000) {
    return `₦${(amount / 1_000_000).toFixed(2)}M`;
  }
  return `₦${amount.toLocaleString()}`;
}

interface ImpactCalculatorProps {
  amount?: number;
  showInput?: boolean;
  compact?: boolean;
  maxItems?: number;
  title?: string;
}

export default function ImpactCalculator({
  amount: initialAmount,
  showInput = true,
  compact = false,
  maxItems = 6,
  title = "What Could This Build?",
}: ImpactCalculatorProps) {
  const [amount, setAmount] = useState(initialAmount || 0);
  const [inputValue, setInputValue] = useState(initialAmount ? formatAmount(initialAmount) : "");

  const parseInput = (value: string) => {
    // Remove ₦ and commas
    let cleaned = value.replace(/[₦,\s]/g, "");

    // Handle suffixes
    if (cleaned.toLowerCase().endsWith("t")) {
      return parseFloat(cleaned.slice(0, -1)) * 1_000_000_000_000;
    } else if (cleaned.toLowerCase().endsWith("b")) {
      return parseFloat(cleaned.slice(0, -1)) * 1_000_000_000;
    } else if (cleaned.toLowerCase().endsWith("m")) {
      return parseFloat(cleaned.slice(0, -1)) * 1_000_000;
    } else if (cleaned.toLowerCase().endsWith("k")) {
      return parseFloat(cleaned.slice(0, -1)) * 1_000;
    }

    return parseFloat(cleaned) || 0;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    setAmount(parseInput(e.target.value));
  };

  const impact = calculateImpact(amount);

  if (compact) {
    return (
      <div className="bg-[#0a0a0a] p-3 rounded">
        <div className="text-[10px] text-gray-500 mb-2 font-mono uppercase">{title}</div>
        <div className="grid grid-cols-2 gap-2">
          {impact.slice(0, maxItems).map((item) => (
            <div key={item.key} className="flex items-center gap-2 text-xs">
              <span>{item.icon}</span>
              <span className="text-[#EBC346] font-mono">{item.count.toLocaleString()}</span>
              <span className="text-gray-500 truncate">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111] border border-c-border p-4 md:p-6">
      <h3 className="text-white font-bold text-lg mb-4">{title}</h3>

      {showInput && (
        <div className="mb-6">
          <label className="text-gray-500 text-xs block mb-2">ENTER AMOUNT</label>
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder="e.g. ₦17.1B or 17100000000"
            className="w-full bg-transparent border border-gray-600 text-white text-lg px-4 py-3 rounded font-mono placeholder:text-gray-600"
          />
          {amount > 0 && (
            <div className="text-gray-500 text-xs mt-2">
              Calculating for: <span className="text-white">{formatAmount(amount)}</span>
            </div>
          )}
        </div>
      )}

      {amount > 0 && impact.length > 0 ? (
        <div className="space-y-3">
          {impact.slice(0, maxItems).map((item) => (
            <div
              key={item.key}
              className="flex items-center justify-between p-3 bg-[#0a0a0a] rounded"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{item.icon}</span>
                <div>
                  <div className="text-white font-medium">{item.label}</div>
                  <div className="text-gray-500 text-xs">{item.description}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-[#EBC346]">
                  {item.count.toLocaleString()}
                </div>
              </div>
            </div>
          ))}

          {/* Shareable summary */}
          <div className="mt-4 p-4 bg-[#1a1a1a] rounded border border-dashed border-gray-700">
            <div className="text-xs text-gray-500 mb-2">SHAREABLE TEXT:</div>
            <p className="text-sm text-gray-300">
              {formatAmount(amount)} could build{" "}
              {impact
                .slice(0, 3)
                .map((i) => `${i.count.toLocaleString()} ${i.label.toLowerCase()}`)
                .join(", or ")}
              . Instead, it&apos;s going to... #Decide9ja
            </p>
            <button
              onClick={() => {
                const text = `${formatAmount(amount)} could build ${impact
                  .slice(0, 3)
                  .map((i) => `${i.count.toLocaleString()} ${i.label.toLowerCase()}`)
                  .join(", or ")}.\n\nInstead, it's going to... 🤔\n\n#Decide9ja #BudgetTransparency`;
                navigator.clipboard.writeText(text);
              }}
              className="mt-2 text-xs text-[#487A3A] hover:underline"
            >
              Copy to clipboard
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          Enter an amount to see what it could build
        </div>
      )}
    </div>
  );
}

// Export the calculation function for use elsewhere
export { calculateImpact, formatAmount, IMPACT_BENCHMARKS };
export type { ImpactResult };
