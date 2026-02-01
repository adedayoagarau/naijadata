import { ImageResponse } from "@vercel/og";
import { NextRequest } from "next/server";

export const runtime = "edge";

// Load Inter font which has good Unicode support including ₦
const interBold = fetch(
  new URL("https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuFuYAZ9hjp18.ttf")
).then((res) => res.arrayBuffer());

const interRegular = fetch(
  new URL("https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hjp18.ttf")
).then((res) => res.arrayBuffer());

// Format amount in Naira - use NGN as fallback for better font compatibility
function formatNaira(amount: number): string {
  if (amount >= 1_000_000_000_000) {
    return `N${(amount / 1_000_000_000_000).toFixed(1)}T`;
  } else if (amount >= 1_000_000_000) {
    return `N${(amount / 1_000_000_000).toFixed(1)}B`;
  } else if (amount >= 1_000_000) {
    return `N${(amount / 1_000_000).toFixed(1)}M`;
  }
  return `N${amount.toLocaleString()}`;
}

// Color mapping for severity
const severityColors: Record<string, { bg: string; text: string }> = {
  CRITICAL: { bg: "#D6453A", text: "#000000" },
  HIGH: { bg: "#164678", text: "#FFFFFF" },
  MEDIUM: { bg: "#EBC346", text: "#000000" },
  LOW: { bg: "#D9D9CD", text: "#000000" },
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;

  // Get parameters from URL
  const entity = searchParams.get("entity") || "Budget Finding";
  const amount = searchParams.get("amount") || "";
  const severity = searchParams.get("severity")?.toUpperCase() || "MEDIUM";
  const type = searchParams.get("type")?.replace(/_/g, " ") || "ANOMALY";
  const description = searchParams.get("description") || "";
  const year = searchParams.get("year") || "2026";

  const colors = severityColors[severity] || severityColors.MEDIUM;

  // Parse amount if it's a number
  const formattedAmount = amount
    ? isNaN(Number(amount))
      ? amount
      : formatNaira(Number(amount))
    : "";

  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#050505",
          padding: "0",
        }}
      >
        {/* Header bar */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "24px 40px",
            borderBottom: "2px solid #222",
          }}
        >
          <span
            style={{
              color: "#FFFFFF",
              fontSize: "24px",
              letterSpacing: "0.2em",
              fontWeight: 400,
            }}
          >
            DECIDE9JA
          </span>
          <span
            style={{
              color: "#666",
              fontSize: "18px",
            }}
          >
            BUDGET TRANSPARENCY
          </span>
        </div>

        {/* Main content */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            padding: "40px",
          }}
        >
          {/* Severity badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "16px",
              marginBottom: "24px",
            }}
          >
            <span
              style={{
                backgroundColor: colors.bg,
                color: colors.text,
                padding: "8px 20px",
                fontSize: "18px",
                fontWeight: 700,
                letterSpacing: "0.1em",
              }}
            >
              {severity}
            </span>
            <span
              style={{
                color: "#888",
                fontSize: "18px",
                textTransform: "uppercase",
              }}
            >
              {type}
            </span>
          </div>

          {/* Amount - large display */}
          {formattedAmount && (
            <div
              style={{
                color: colors.bg,
                fontSize: "96px",
                fontWeight: 700,
                marginBottom: "16px",
                lineHeight: 1,
              }}
            >
              {formattedAmount}
            </div>
          )}

          {/* Entity name */}
          <div
            style={{
              color: "#FFFFFF",
              fontSize: "48px",
              fontWeight: 600,
              marginBottom: "20px",
              lineHeight: 1.2,
              maxWidth: "90%",
            }}
          >
            {entity.length > 60 ? entity.substring(0, 60) + "..." : entity}
          </div>

          {/* Description */}
          {description && (
            <div
              style={{
                color: "#AAAAAA",
                fontSize: "24px",
                lineHeight: 1.4,
                maxWidth: "85%",
              }}
            >
              {description.length > 150
                ? description.substring(0, 150) + "..."
                : description}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "24px 40px",
            borderTop: "2px solid #222",
          }}
        >
          <span
            style={{
              color: "#EBC346",
              fontSize: "20px",
              fontWeight: 600,
            }}
          >
            #Decide9ja #BudgetTransparency
          </span>
          <span
            style={{
              color: "#666",
              fontSize: "18px",
            }}
          >
            {year} BUDGET
          </span>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      fonts: [
        {
          name: "Inter",
          data: await interRegular,
          weight: 400,
          style: "normal",
        },
        {
          name: "Inter",
          data: await interBold,
          weight: 700,
          style: "normal",
        },
      ],
    }
  );
}
