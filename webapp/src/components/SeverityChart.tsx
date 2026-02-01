"use client";

interface ChartData {
  label: string;
  count: number;
  amount: number;
  color: string;
}

interface SeverityChartProps {
  data: ChartData[];
  title?: string;
}

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

export default function SeverityChart({ data, title = "BY SEVERITY" }: SeverityChartProps) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);
  const totalAmount = data.reduce((sum, d) => sum + d.amount, 0);

  return (
    <div className="bg-[#111] border border-c-border p-4">
      <div className="text-xs text-gray-500 font-mono mb-3">{title}</div>
      <div className="space-y-2">
        {data.map((item) => (
          <div key={item.label} className="flex items-center gap-3">
            <div className="w-16 text-xs text-gray-400">{item.label}</div>
            <div className="flex-1 h-6 bg-[#0a0a0a] rounded overflow-hidden">
              <div
                className="h-full transition-all duration-500"
                style={{
                  width: `${(item.count / maxCount) * 100}%`,
                  backgroundColor: item.color,
                }}
              />
            </div>
            <div className="w-12 text-right text-sm font-mono text-white">{item.count}</div>
            <div className="w-20 text-right text-xs text-gray-500">{formatAmount(item.amount)}</div>
          </div>
        ))}
      </div>
      <div className="mt-3 pt-3 border-t border-[#222] flex justify-between text-xs">
        <span className="text-gray-500">TOTAL FLAGGED</span>
        <span className="text-white font-mono">{formatAmount(totalAmount)}</span>
      </div>
    </div>
  );
}
