import { Metadata } from "next";

// Format amount in Naira
function formatNaira(amount: number): string {
  if (amount >= 1_000_000_000_000) {
    return `₦${(amount / 1_000_000_000_000).toFixed(1)}T`;
  } else if (amount >= 1_000_000_000) {
    return `₦${(amount / 1_000_000_000).toFixed(1)}B`;
  } else if (amount >= 1_000_000) {
    return `₦${(amount / 1_000_000).toFixed(1)}M`;
  }
  return `₦${amount.toLocaleString()}`;
}

// Fetch finding data for metadata
async function getFinding(id: string) {
  // In production, this would fetch from a database or API
  // For now, we use demo data
  const findings = [
    {
      id: "1",
      type: "MANDATE_VIOLATION",
      entity: "National Intelligence Agency",
      description: "Security agency allocated ₦31.1B for hospital construction",
      amount: 31_104_141_419,
      severity: "CRITICAL",
      year: 2026,
    },
    {
      id: "2",
      type: "YOY_VARIANCE",
      entity: "National Assembly",
      description: "320% increase in travel allowances",
      amount: 22_490_000_000,
      severity: "HIGH",
      year: 2026,
    },
    {
      id: "3",
      type: "ROUND_NUMBER",
      entity: "Ministry of Works",
      description: "Exact ₦10B allocation suggests estimation",
      amount: 10_000_000_000,
      severity: "MEDIUM",
      year: 2026,
    },
    {
      id: "4",
      type: "CROSS_MDA_OUTLIER",
      entity: "Office of the NSA",
      description: "Spending 8.5x median for security equipment",
      amount: 45_000_000_000,
      severity: "CRITICAL",
      year: 2026,
    },
  ];

  return findings.find((f) => f.id === id) || findings[Number(id)] || null;
}

type Props = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const finding = await getFinding(id);

  if (!finding) {
    return {
      title: "Finding Not Found | Decide9ja",
      description: "The requested finding could not be found.",
    };
  }

  const title = `${finding.entity} - ${formatNaira(finding.amount)} | Decide9ja`;
  const description = `${finding.severity}: ${finding.description}. ${finding.year} Nigerian Budget.`;

  // Build OG image URL
  const ogImageUrl = `/api/og?entity=${encodeURIComponent(finding.entity)}&amount=${finding.amount}&severity=${finding.severity}&type=${finding.type}&description=${encodeURIComponent(finding.description || "")}&year=${finding.year}`;

  return {
    title,
    description,
    keywords: [
      "Nigeria",
      "budget",
      "transparency",
      finding.entity,
      finding.type,
      "Decide9ja",
    ],
    openGraph: {
      title,
      description,
      type: "article",
      images: [
        {
          url: ogImageUrl,
          width: 1200,
          height: 630,
          alt: `${finding.entity} - Budget Finding`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [ogImageUrl],
    },
  };
}

export default function FindingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
