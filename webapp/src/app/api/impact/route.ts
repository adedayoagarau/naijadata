import { NextRequest, NextResponse } from "next/server";

// What Nigerian money can build
const IMPACT_BENCHMARKS: Record<
  string,
  { cost: number; label: string; description: string }
> = {
  primary_school: {
    cost: 150_000_000,
    label: "Primary Schools",
    description: "6 classrooms, 240 students each",
  },
  health_center: {
    cost: 150_000_000,
    label: "Health Centers",
    description: "Serves 10,000 people",
  },
  borehole: {
    cost: 5_000_000,
    label: "Boreholes",
    description: "Clean water for 500 people",
  },
  ambulance: {
    cost: 50_000_000,
    label: "Ambulances",
    description: "Fully equipped emergency vehicle",
  },
  road_km: {
    cost: 150_000_000,
    label: "Km of Road",
    description: "Paved road construction",
  },
  affordable_house: {
    cost: 15_000_000,
    label: "Houses",
    description: "Affordable 2-bedroom home",
  },
  child_vaccination: {
    cost: 15_000,
    label: "Child Vaccinations",
    description: "Full immunization program",
  },
  malaria_treatment: {
    cost: 5_000,
    label: "Malaria Treatments",
    description: "Full treatment course",
  },
  yearly_minimum_wage: {
    cost: 840_000,
    label: "Years of Min. Wage",
    description: "₦70,000/month for a worker",
  },
  university_scholarship: {
    cost: 500_000,
    label: "Scholarships",
    description: "1-year university scholarship",
  },
};

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

function calculateImpact(amount: number) {
  return Object.entries(IMPACT_BENCHMARKS)
    .map(([key, { cost, label, description }]) => ({
      key,
      count: Math.floor(amount / cost),
      label,
      description,
      unit_cost: cost,
      total_value: Math.floor(amount / cost) * cost,
    }))
    .filter((item) => item.count > 0)
    .sort((a, b) => b.count - a.count);
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const amountStr = searchParams.get("amount");

  if (!amountStr) {
    return NextResponse.json({
      error: "Missing amount parameter",
      usage: "/api/impact?amount=17100000000",
      benchmarks: IMPACT_BENCHMARKS,
    });
  }

  // Parse amount (handle suffixes like B, M, T)
  let amount = 0;
  const cleaned = amountStr.replace(/[₦,\s]/g, "").toLowerCase();

  if (cleaned.endsWith("t")) {
    amount = parseFloat(cleaned.slice(0, -1)) * 1_000_000_000_000;
  } else if (cleaned.endsWith("b")) {
    amount = parseFloat(cleaned.slice(0, -1)) * 1_000_000_000;
  } else if (cleaned.endsWith("m")) {
    amount = parseFloat(cleaned.slice(0, -1)) * 1_000_000;
  } else if (cleaned.endsWith("k")) {
    amount = parseFloat(cleaned.slice(0, -1)) * 1_000;
  } else {
    amount = parseFloat(cleaned);
  }

  if (isNaN(amount) || amount <= 0) {
    return NextResponse.json({ error: "Invalid amount" }, { status: 400 });
  }

  const impact = calculateImpact(amount);

  // Generate shareable text
  const topImpacts = impact.slice(0, 3);
  const shareableText = `${formatNaira(amount)} could build ${topImpacts
    .map((i) => `${i.count.toLocaleString()} ${i.label.toLowerCase()}`)
    .join(", or ")}. #Decide9ja`;

  return NextResponse.json({
    amount,
    formatted_amount: formatNaira(amount),
    impact,
    shareable_text: shareableText,
    twitter_url: `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareableText)}`,
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { amount, context } = body;

    if (!amount || amount <= 0) {
      return NextResponse.json({ error: "Invalid amount" }, { status: 400 });
    }

    const impact = calculateImpact(amount);

    // Generate contextual shareable text
    let shareableText = "";
    if (context) {
      shareableText = `🚨 ${context}\n\n${formatNaira(amount)} could instead build:\n`;
      impact.slice(0, 3).forEach((i) => {
        shareableText += `• ${i.count.toLocaleString()} ${i.label.toLowerCase()}\n`;
      });
      shareableText += `\n#Decide9ja #BudgetTransparency`;
    } else {
      shareableText = `${formatNaira(amount)} could build ${impact
        .slice(0, 3)
        .map((i) => `${i.count.toLocaleString()} ${i.label.toLowerCase()}`)
        .join(", or ")}. #Decide9ja`;
    }

    return NextResponse.json({
      amount,
      formatted_amount: formatNaira(amount),
      impact,
      shareable_text: shareableText,
      twitter_url: `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareableText)}`,
      whatsapp_url: `https://wa.me/?text=${encodeURIComponent(shareableText)}`,
    });
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
