"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Overview" },
  { href: "/leaderboards", label: "Leaderboards" },
  { href: "/player", label: "Player Lookup" },
  { href: "/data-journey", label: "Data Journey" },
  { href: "/methodology", label: "Methodology" },
  { href: "/observability", label: "Observability" },
];

export function SiteNav() {
  const pathname = usePathname();
  return (
    <header className="site-shell">
      <div className="masthead">
        <div className="masthead-inner">
          <Link href="/" className="brand" aria-label="ChessKE Atlas home">
            <span className="edition-line">Live · Chess.com API</span>
            <span className="site-title">
              Chess<span>KE</span> Atlas
            </span>
            <span className="site-subtitle">Kenya online chess intelligence platform</span>
          </Link>
          <div className="masthead-right">
            <span className="sync-badge">Live</span>
            <span>Rolling discovery ledger</span>
            <span>Production API</span>
          </div>
        </div>
      </div>
      <nav className="site-nav" aria-label="Primary navigation">
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
