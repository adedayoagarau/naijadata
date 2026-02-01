import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface BudgetItem {
  mda?: string;
  budget_code?: string;
  description?: string;
  amount?: number;
  year?: number;
  type?: string;
  sector?: string;
}

interface Aggregation {
  key: string;
  total: number;
  count: number;
  items?: BudgetItem[];
}

// Load budget items from various sources
function loadBudgetItems(): BudgetItem[] {
  const paths = [
    path.join(process.cwd(), "..", "data", "master", "all_items.json"),
    path.join(process.cwd(), "..", "extracted", "master_budget_data.json"),
    path.join(process.cwd(), "..", "data", "federal", "2026", "budget_items.json"),
    path.join(process.cwd(), "..", "data", "federal", "2025", "budget_items.json"),
  ];

  const allItems: BudgetItem[] = [];

  for (const p of paths) {
    try {
      if (fs.existsSync(p)) {
        const data = JSON.parse(fs.readFileSync(p, "utf-8"));
        if (Array.isArray(data)) {
          allItems.push(...data);
        } else if (data.items) {
          allItems.push(...data.items);
        }
        console.log(`Loaded items from: ${p}`);
        break; // Use first available source
      }
    } catch (e) {
      console.error(`Failed to load ${p}:`, e);
    }
  }

  return allItems;
}

// Load pre-computed aggregations if available
function loadPrecomputedAggregations(type: string): Record<string, Aggregation> | null {
  const aggPath = path.join(process.cwd(), "..", "data", "aggregations", `by_${type}.json`);
  try {
    if (fs.existsSync(aggPath)) {
      return JSON.parse(fs.readFileSync(aggPath, "utf-8"));
    }
  } catch (e) {
    console.error(`Failed to load aggregation ${type}:`, e);
  }
  return null;
}

// Aggregate by field
function aggregateBy(items: BudgetItem[], field: keyof BudgetItem, year?: number): Record<string, Aggregation> {
  const result: Record<string, Aggregation> = {};

  for (const item of items) {
    if (year && item.year !== year) continue;

    const key = String(item[field] || "Unknown");
    const amount = item.amount || 0;

    if (!result[key]) {
      result[key] = { key, total: 0, count: 0 };
    }
    result[key].total += amount;
    result[key].count += 1;
  }

  return result;
}

// Format amount
function formatNaira(amount: number): string {
  if (amount >= 1_000_000_000_000) {
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`;
  } else if (amount >= 1_000_000_000) {
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`;
  } else if (amount >= 1_000_000) {
    return `₦${(amount / 1_000_000).toFixed(2)}M`;
  }
  return `₦${amount.toLocaleString()}`;
}

// Budget code descriptions
const BUDGET_CODE_NAMES: Record<string, string> = {
  "23010105": "Motor Vehicles (Convoys)",
  "22020801": "International Travel",
  "22020802": "Local Travel",
  "22020803": "Transport & Escort",
  "22021000": "Miscellaneous Expenses",
  "22020901": "Honorarium & Sitting Allowances",
  "2205": "Consultancy Services",
  "2302": "Construction Projects",
  "2303": "Rehabilitation",
  "2101": "Salaries & Wages",
  "2102": "Allowances",
};

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const by = searchParams.get("by") || "budget_code"; // budget_code, mda, sector, year
  const year = searchParams.get("year") ? parseInt(searchParams.get("year")!) : undefined;
  const code = searchParams.get("code"); // Filter by specific budget code
  const limit = searchParams.get("limit") ? parseInt(searchParams.get("limit")!) : 50;

  try {
    // Try pre-computed aggregations first
    const precomputed = loadPrecomputedAggregations(by);
    let aggregations: Record<string, Aggregation>;

    if (precomputed) {
      aggregations = precomputed;
    } else {
      // Compute on the fly
      const items = loadBudgetItems();
      if (items.length === 0) {
        return NextResponse.json({
          error: "No budget data available",
          aggregations: [],
        });
      }
      aggregations = aggregateBy(items, by as keyof BudgetItem, year);
    }

    // Filter by code if specified
    if (code) {
      aggregations = Object.fromEntries(
        Object.entries(aggregations).filter(([key]) => key.startsWith(code))
      );
    }

    // Convert to array and sort by total
    let results = Object.values(aggregations)
      .map((agg) => ({
        ...agg,
        formatted_total: formatNaira(agg.total),
        name: BUDGET_CODE_NAMES[agg.key] || agg.key,
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, limit);

    // Calculate summary
    const totalAmount = results.reduce((sum, r) => sum + r.total, 0);
    const totalItems = results.reduce((sum, r) => sum + r.count, 0);

    return NextResponse.json({
      by,
      year: year || "all",
      count: results.length,
      total_amount: totalAmount,
      formatted_total: formatNaira(totalAmount),
      total_items: totalItems,
      aggregations: results,
    });
  } catch (error) {
    console.error("Aggregation error:", error);
    return NextResponse.json(
      { error: "Failed to compute aggregations" },
      { status: 500 }
    );
  }
}

// POST for custom queries
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { codes, year, include_items } = body;

    const items = loadBudgetItems();
    if (items.length === 0) {
      return NextResponse.json({ error: "No budget data available" });
    }

    // Filter by codes and year
    let filtered = items;
    if (year) {
      filtered = filtered.filter((item) => item.year === year);
    }
    if (codes && Array.isArray(codes)) {
      filtered = filtered.filter((item) =>
        codes.some((code: string) => String(item.budget_code || "").startsWith(code))
      );
    }

    // Aggregate
    const total = filtered.reduce((sum, item) => sum + (item.amount || 0), 0);
    const mdas = [...new Set(filtered.map((item) => item.mda))];

    const result: {
      total: number;
      formatted_total: string;
      count: number;
      mda_count: number;
      mdas: string[];
      items?: BudgetItem[];
    } = {
      total,
      formatted_total: formatNaira(total),
      count: filtered.length,
      mda_count: mdas.length,
      mdas: mdas.filter(Boolean) as string[],
    };

    if (include_items) {
      result.items = filtered.slice(0, 100); // Limit items returned
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error("Aggregation POST error:", error);
    return NextResponse.json(
      { error: "Failed to process query" },
      { status: 500 }
    );
  }
}
