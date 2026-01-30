import { NextRequest, NextResponse } from "next/server";
import { ImageResponse } from "next/og";

export const runtime = "edge";

export async function POST(request: NextRequest) {
  try {
    const { title, amount, description, comparison } = await request.json();

    // Calculate impact
    const amountNum = parseAmount(amount);
    const schools = Math.floor(amountNum / 150_000_000);
    const healthCenters = Math.floor(amountNum / 150_000_000);
    const boreholes = Math.floor(amountNum / 5_000_000);

    return new ImageResponse(
      (
        <div
          style={{
            height: "100%",
            width: "100%",
            display: "flex",
            flexDirection: "column",
            backgroundColor: "#050505",
            padding: "40px",
            fontFamily: "monospace",
          }}
        >
          {/* Header */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: "30px",
            }}
          >
            <div
              style={{
                fontSize: "48px",
                fontWeight: "bold",
                color: "white",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <span>DECIDE</span>
              <span style={{ color: "#25D366" }}>9JA</span>
            </div>
            <div
              style={{
                backgroundColor: "#25D366",
                color: "black",
                padding: "8px 16px",
                fontSize: "14px",
                fontWeight: "bold",
              }}
            >
              BUDGET ALERT
            </div>
          </div>

          {/* Main content */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                fontSize: "16px",
                color: "#888",
                marginBottom: "10px",
                textTransform: "uppercase",
              }}
            >
              {title}
            </div>

            <div
              style={{
                fontSize: "64px",
                fontWeight: "bold",
                color: "white",
                marginBottom: "20px",
              }}
            >
              {amount}
            </div>

            {comparison && (
              <div
                style={{
                  backgroundColor: "white",
                  color: "black",
                  padding: "8px 16px",
                  fontSize: "24px",
                  fontWeight: "bold",
                  display: "inline-block",
                  marginBottom: "20px",
                  alignSelf: "flex-start",
                }}
              >
                {comparison}
              </div>
            )}

            <div
              style={{
                fontSize: "18px",
                color: "#ccc",
                lineHeight: 1.5,
                maxWidth: "90%",
              }}
            >
              {description}
            </div>
          </div>

          {/* Impact section */}
          <div
            style={{
              borderTop: "1px solid #333",
              paddingTop: "20px",
              marginTop: "20px",
            }}
          >
            <div
              style={{
                fontSize: "14px",
                color: "#888",
                marginBottom: "10px",
              }}
            >
              THIS AMOUNT COULD BUILD:
            </div>
            <div
              style={{
                display: "flex",
                gap: "30px",
                fontSize: "16px",
                color: "white",
              }}
            >
              <span>🏫 {schools.toLocaleString()} schools</span>
              <span>🏥 {healthCenters.toLocaleString()} health centers</span>
              <span>🚰 {boreholes.toLocaleString()} boreholes</span>
            </div>
          </div>

          {/* Footer */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: "30px",
              paddingTop: "20px",
              borderTop: "1px solid #333",
            }}
          >
            <div style={{ fontSize: "14px", color: "#666" }}>
              Source: 2026 Federal Budget Bill
            </div>
            <div style={{ fontSize: "14px", color: "#25D366" }}>
              #Decide9ja #OpenBudget
            </div>
          </div>
        </div>
      ),
      {
        width: 1200,
        height: 630,
      }
    );
  } catch (error) {
    console.error("Card generation error:", error);
    return NextResponse.json(
      { error: "Failed to generate card" },
      { status: 500 }
    );
  }
}

function parseAmount(amount: string): number {
  const cleaned = amount.replace(/[₦,\s]/g, "").toUpperCase();

  if (cleaned.includes("TRILLION")) {
    return parseFloat(cleaned) * 1_000_000_000_000;
  }
  if (cleaned.includes("BILLION")) {
    return parseFloat(cleaned) * 1_000_000_000;
  }
  if (cleaned.includes("MILLION")) {
    return parseFloat(cleaned) * 1_000_000;
  }

  return parseFloat(cleaned) || 0;
}
