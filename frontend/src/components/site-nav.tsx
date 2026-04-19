"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Atlas" },
  { href: "/leaderboards", label: "Leaderboards" },
  { href: "/player", label: "Player" },
  { href: "/methodology", label: "Methodology" },
  { href: "/observability", label: "Observability" },
];

export function SiteNav() {
  const pathname = usePathname();
  return (
    <header className="site-nav">
      <Link href="/" className="brand">
        <span className="brand-mark">♞</span>
        <span>ChessKE Atlas</span>
      </Link>
      <nav>
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`nav-link ${active ? "active" : ""}`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
