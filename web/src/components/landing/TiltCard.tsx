"use client";

import { useRef, type ReactNode } from "react";

/** A card that tilts towards the pointer in perspective (CSS only; still with reduced motion). */
export function TiltCard({ children, className }: { children: ReactNode; className?: string }) {
  const el = useRef<HTMLDivElement>(null);
  const move = (e: React.PointerEvent) => {
    const r = el.current?.getBoundingClientRect();
    if (!r || !el.current) return;
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    el.current.style.setProperty("--rx", `${(-y * 10).toFixed(2)}deg`);
    el.current.style.setProperty("--ry", `${(x * 12).toFixed(2)}deg`);
    el.current.style.setProperty("--gx", `${((x + 0.5) * 100).toFixed(1)}%`);
    el.current.style.setProperty("--gy", `${((y + 0.5) * 100).toFixed(1)}%`);
  };
  const leave = () => {
    el.current?.style.setProperty("--rx", "0deg");
    el.current?.style.setProperty("--ry", "0deg");
  };
  return (
    <div ref={el} className={`tilt ${className ?? ""}`} onPointerMove={move} onPointerLeave={leave}>
      {children}
    </div>
  );
}
