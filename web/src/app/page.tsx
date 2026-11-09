import { Suspense } from "react";
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
        <ApiStatusBadge />
      </header>
      <Suspense fallback={null}>
        <Viewer />
      </Suspense>
    </main>
  );
}
