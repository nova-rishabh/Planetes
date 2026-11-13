import Link from "next/link";
import { ApiStatusBadge } from "./ApiStatusBadge";

const LINKS = [
  { href: "/viewer", label: "Viewer" },
  { href: "/planet-x", label: "Planet X check" },
  { href: "/validation", label: "Validation" },
  { href: "/about", label: "About" },
];

/** Top bar shared by every page: wordmark, the four sections, live API status. */
export function SiteNav({ current }: { current?: string }) {
  return (
    <nav className="sitenav" aria-label="Main">
      <Link href="/" className="sitenav-mark">
        Planetes
      </Link>
      <ul className="sitenav-links">
        {LINKS.map((l) => (
          <li key={l.href}>
            <Link href={l.href} aria-current={current === l.href ? "page" : undefined}>
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
      <ApiStatusBadge />
    </nav>
  );
}
