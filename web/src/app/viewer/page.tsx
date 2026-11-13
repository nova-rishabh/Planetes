import { Suspense } from "react";
import type { Metadata } from "next";
import { SiteNav } from "@/components/SiteNav";
import { Viewer } from "@/components/Viewer";

export const metadata: Metadata = {
  title: "Viewer · Planetes",
  description: "Type a sky position or pick a benchmark and play every SPHEREx image of it as a time-lapse.",
};

export default function ViewerPage() {
  return (
    <main className="app">
      <SiteNav current="/viewer" />
      <header className="view-intro">
        <h1>Viewer</h1>
        <p className="tagline">Every NASA SPHEREx infrared image of one patch of sky, played as a time-lapse.</p>
      </header>
      <Suspense fallback={null}>
        <Viewer />
      </Suspense>
    </main>
  );
}
