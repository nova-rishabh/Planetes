import type { Metadata } from "next";
import { Suspense } from "react";
import { Viewer } from "@/components/Viewer";

export const metadata: Metadata = { title: "Planetes · embed" };

/** Same view and URL parameters as the main page, minimal chrome, for iframes (docs/03 §2). */
export default function Embed() {
  return (
    <main className="app app-embed">
      <Suspense fallback={null}>
        <Viewer embed />
      </Suspense>
      <p className="embed-credit">
        <a href="https://planetes.divergit.com" target="_blank" rel="noreferrer">Planetes</a> · NASA SPHEREx data via IRSA
      </p>
    </main>
  );
}
