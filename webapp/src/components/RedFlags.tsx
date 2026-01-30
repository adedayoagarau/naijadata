const redFlags = [
  {
    severity: "SEVERE",
    severityColor: "text-red-500 border-red-900",
    icon: "!",
    iconColor: "text-red-500",
    title: "NIA HOSPITAL REPAIRS",
    description:
      "National Intelligence Agency allocated ₦31.1B for hospital repairs - 46x more than Health Ministry HQ spends on same item.",
  },
  {
    severity: "SEVERE",
    severityColor: "text-red-500 border-red-900",
    icon: "!",
    iconColor: "text-red-500",
    title: "POLICE ACADEMY SCHOOL MEALS",
    description:
      "Nigeria Police Academy Wudil budgeting ₦5.9B for school meal subsidies - outside their mandate.",
  },
  {
    severity: "WARNING",
    severityColor: "text-yellow-500 border-yellow-900",
    icon: "?",
    iconColor: "text-yellow-500",
    title: "ARMY ROAD CONSTRUCTION",
    description:
      "Nigerian Army allocated ₦3.72B for road construction - should be under Federal Ministry of Works.",
  },
  {
    severity: "WARNING",
    severityColor: "text-yellow-500 border-yellow-900",
    icon: "?",
    iconColor: "text-yellow-500",
    title: "NAVY BUILDING SCHOOLS",
    description:
      "Nigerian Navy budgeting ₦3.64B for public school construction - outside military mandate.",
  },
  {
    severity: "NOTICE",
    severityColor: "text-blue-500 border-blue-900",
    icon: "i",
    iconColor: "text-blue-500",
    title: "NASS TRAVEL BUDGET",
    description:
      "National Assembly travel budget of ₦22.49B for 469 legislators - averaging ₦47.9M per lawmaker.",
  },
];

export function RedFlags() {
  return (
    <section className="p-4">
      <h3 className="font-pixel text-2xl md:text-3xl mb-4 flex items-center gap-2">
        RED_FLAGS{" "}
        <span className="block w-2 h-2 bg-red-600 animate-pulse rounded-full" />
      </h3>

      <div className="border-t border-white">
        {redFlags.map((flag, index) => (
          <div
            key={index}
            className="py-3 border-b border-gray-800 flex items-start gap-3 cursor-pointer hover:bg-[#0a0a0a] transition-colors"
          >
            <div className={`font-mono font-bold text-lg mt-1 ${flag.iconColor}`}>
              {flag.icon}
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-baseline mb-1">
                <span className="font-bold text-sm">{flag.title}</span>
                <span className={`text-xs border px-1 ${flag.severityColor}`}>
                  {flag.severity}
                </span>
              </div>
              <p className="text-[10px] text-gray-400 uppercase leading-relaxed">
                {flag.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      <button className="w-full mt-4 border border-white py-2 font-mono text-sm uppercase hover:bg-white hover:text-black transition-colors">
        [ VIEW ALL 177 RED FLAGS ]
      </button>
    </section>
  );
}
