"use client";

import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { use3DMode } from "./three/scroll";

/**
 * A 3D figure that only mounts when it comes near the screen, and shows `flat` when 3D can't run.
 * `progress` runs 0..1 while the figure crosses the viewport (bottom edge in → top edge out).
 */
export function LazyScene({
  className,
  flat,
  label,
  children,
}: {
  className?: string;
  flat: ReactNode;
  label?: string;
  children: (ctx: { narrow: boolean; progress: RefObject<number> }) => ReactNode;
}) {
  const { mode, narrow, ready } = use3DMode(true);
  const box = useRef<HTMLDivElement>(null);
  const progress = useRef(0);
  const [near, setNear] = useState(false);

  useEffect(() => {
    if (mode !== "3d" || !box.current) return;
    const el = box.current;
    const io = new IntersectionObserver(([e]) => e?.isIntersecting && setNear(true), { rootMargin: "300px 0px" });
    io.observe(el);
    const onScroll = () => {
      const r = el.getBoundingClientRect();
      const vh = window.innerHeight;
      progress.current = Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height)));
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      io.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
  }, [mode]);

  if (mode === "flat") return <>{flat}</>;
  return (
    <div ref={box} className={className} role={label ? "img" : undefined} aria-label={label}>
      {/* The ref is passed through (read only inside the scene's frame loop), not read here. */}
      {/* eslint-disable-next-line react-hooks/refs */}
      {ready && near && children({ narrow, progress })}
    </div>
  );
}
