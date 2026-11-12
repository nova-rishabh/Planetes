import { Suspense } from "react";
import Link from "next/link";
import { ApiStatusBadge } from "@/components/ApiStatusBadge";
import { Viewer } from "@/components/Viewer";

export default function Home() {
  return (
    <main className="app">
      <header className="masthead">
        <div>
          <h1>Planetes</h1>
          <p className="tagline">
            Every NASA SPHEREx infrared image of one patch of sky, played as a time-lapse.
          </p>
        </div>
        <div className="masthead-side">
          <Link href="/about" className="btn">
            About
          </Link>
          <Link href="/validation" className="btn">
            Validation
          </Link>
          <Link href="/planet-x" className="btn">
            Planet X check
          </Link>
          <ApiStatusBadge />
        </div>
      </header>
      <Suspense fallback={null}>
        <Viewer />
      </Suspense>
    </main>
  );
}
