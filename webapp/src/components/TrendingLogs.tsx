const trendingItems = [
  {
    id: "#8892",
    tag: "SCANDAL",
    tagStyle: "bg-white text-black",
    title: "NIA HOSPITAL CONSTRUCTION ANOMALY",
    amount: "₦31B",
    variance: "+4600%",
    image: "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?q=80&w=600&auto=format&fit=crop",
  },
  {
    id: "#4412",
    tag: "AUDIT",
    tagStyle: "border border-white text-white",
    title: "NASS TRAVEL VS HEALTH BUDGET",
    amount: "₦22.5B",
    variance: "+200%",
    image: "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?q=80&w=600&auto=format&fit=crop",
  },
  {
    id: "#3301",
    tag: "ANOMALY",
    tagStyle: "bg-red-600 text-white",
    title: "POLICE ACADEMY SCHOOL MEALS",
    amount: "₦5.9B",
    variance: "N/A",
    image: "https://images.unsplash.com/photo-1567521464027-f127ff144326?q=80&w=600&auto=format&fit=crop",
  },
  {
    id: "#2210",
    tag: "WARNING",
    tagStyle: "bg-yellow-600 text-black",
    title: "ARMY ROAD CONSTRUCTION",
    amount: "₦3.7B",
    variance: "+150%",
    image: "https://images.unsplash.com/photo-1545558014-8692077e9b5c?q=80&w=600&auto=format&fit=crop",
  },
];

export function TrendingLogs() {
  return (
    <section className="py-6 pl-4 border-b border-white overflow-hidden">
      <div className="flex justify-between pr-4 mb-2 items-end">
        <h3 className="font-pixel text-2xl md:text-3xl">TRENDING_LOGS</h3>
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-white" />
          <div className="w-2 h-2 border border-white" />
          <div className="w-2 h-2 border border-white" />
        </div>
      </div>

      <div className="flex overflow-x-auto gap-4 no-scrollbar pr-4 pb-4">
        {trendingItems.map((item) => (
          <div
            key={item.id}
            className="min-w-[280px] border border-white bg-[#0a0a0a] flex flex-col relative cursor-pointer hover:bg-[#111] transition-colors"
          >
            <div className="h-40 w-full overflow-hidden relative border-b border-white">
              <img
                src={item.image}
                className="w-full h-full object-cover img-dither"
                alt={item.title}
              />
              <div className="absolute top-2 right-2 w-12 h-12 rounded-full border border-white opacity-80 flex items-center justify-center">
                <div className="w-full h-[1px] bg-white absolute" />
                <div className="h-full w-[1px] bg-white absolute" />
              </div>
            </div>
            <div className="p-3">
              <div className="flex justify-between text-[10px] mb-1">
                <span className={`px-1 ${item.tagStyle}`}>{item.tag}</span>
                <span>{item.id}</span>
              </div>
              <h4 className="font-bold font-mono text-sm leading-tight mb-2">
                {item.title}
              </h4>
              <div className="text-[10px] text-gray-400 grid grid-cols-2 gap-2 border-t border-gray-800 pt-2">
                <div>AMT: {item.amount}</div>
                <div>VAR: {item.variance}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
