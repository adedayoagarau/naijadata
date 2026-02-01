"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface HeaderProps {
  findingsCount?: number;
}

export function Header({ findingsCount }: HeaderProps) {
  const pathname = usePathname();
  const today = new Date();
  const dateStr = `${String(today.getMonth() + 1).padStart(2, "0")}.${String(
    today.getDate()
  ).padStart(2, "0")}.${String(today.getFullYear()).slice(-2)}`;

  const navItems = [
    { href: "/red-flags", label: findingsCount ? `RED FLAGS (${findingsCount})` : "RED FLAGS" },
    { href: "/compare", label: "COMPARE" },
    { href: "/explore", label: "EXPLORE" },
    { href: "/impact", label: "IMPACT" },
    { href: "/about", label: "ABOUT" },
  ];

  return (
    <header className="bg-c-black text-gray-500 px-4 md:px-8 py-4 md:py-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-2 font-display text-xs tracking-wide border-b border-c-border flex-shrink-0">
      <Link
        href="/"
        className="text-white font-normal text-xs tracking-[0.2em] uppercase hover:text-gray-300 transition-colors"
      >
        Decide9ja // Budget Transparency DB
      </Link>
      <nav className="flex gap-4 md:gap-16 text-[10px] md:text-xs">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`transition-colors ${
                isActive ? "text-white" : "text-gray-500 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
        <span className="text-gray-600">{dateStr}</span>
      </nav>
    </header>
  );
}

export default Header;
