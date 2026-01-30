export function Marquee() {
  const alerts = [
    "ANOMALY DETECTED: NIA ₦31B HOSPITAL SCANDAL",
    "POLICE ACADEMY MEAL FRAUD DETECTED",
    "NASS TRAVEL BUDGET EXCEEDS HEALTH",
    "177 RED FLAGS FOUND IN 2026 BUDGET",
    "₦86B SUSPICIOUS CROSS-MDA SPENDING",
  ];

  const text = alerts.join(" /// ");

  return (
    <div className="border-b border-white py-1 bg-[#25D366] text-black overflow-hidden font-mono text-xs font-bold uppercase marquee-container">
      <div className="marquee-content">
        {text} /// {text} ///
      </div>
    </div>
  );
}
