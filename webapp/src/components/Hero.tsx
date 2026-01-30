"use client";

export function Hero() {
  return (
    <section className="px-4 lg:px-8 py-8 lg:py-12 border-b border-gray-800">
      <div className="max-w-3xl">
        <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4">
          See where Nigeria&apos;s{" "}
          <span className="text-[#25D366]">₦28.7 trillion</span>{" "}
          budget actually goes
        </h1>
        <p className="text-gray-400 text-base md:text-lg leading-relaxed">
          We analyzed 2,790 pages of the 2026 federal budget and found{" "}
          <span className="text-white font-medium">₦86 billion</span> in suspicious spending
          across <span className="text-white font-medium">177 anomalies</span>.
          Search any ministry, compare spending, and share what you find.
        </p>
      </div>
    </section>
  );
}
