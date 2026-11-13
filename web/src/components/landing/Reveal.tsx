"use client";

import type { ReactNode } from "react";
import { useInView } from "./useInView";

/** Fades and lifts its children in the first time they scroll into view (static under reduced motion, via CSS). */
export function Reveal({ children, className = "", as: Tag = "div" }: { children: ReactNode; className?: string; as?: "div" | "section" | "li" }) {
  const [ref, inView] = useInView<HTMLDivElement>(false, 0.2);
  return (
    <Tag ref={ref as never} className={`reveal ${className}`} data-in={inView}>
      {children}
    </Tag>
  );
}
