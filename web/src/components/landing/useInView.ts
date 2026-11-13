"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

/** True once the element has scrolled into view (and, with `track`, false again when it leaves). */
export function useInView<T extends Element>(track = false, threshold = 0.35) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      setInView(true);
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry) return;
        if (entry.isIntersecting) setInView(true);
        else if (track) setInView(false);
      },
      { threshold },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [track, threshold]);
  return [ref, inView] as const;
}

const QUERY = "(prefers-reduced-motion: reduce)";
function subscribe(cb: () => void) {
  const mq = window.matchMedia?.(QUERY);
  mq?.addEventListener("change", cb);
  return () => mq?.removeEventListener("change", cb);
}

/** prefers-reduced-motion, kept in sync with the OS setting (false while rendering on the server). */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia?.(QUERY).matches ?? false,
    () => false,
  );
}
