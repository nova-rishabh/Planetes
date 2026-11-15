"use client";

import { useEffect, useState } from "react";
import { badgeFor, fetchHealth, type HealthState } from "@/lib/health";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

/** Live badge for GET ${NEXT_PUBLIC_API_BASE}/api/health. */
export function ApiStatusBadge() {
  const [state, setState] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(API_BASE, controller.signal)
      .then(setState)
      .catch(() => {
        /* aborted on unmount */
      });
    return () => controller.abort();
  }, []);

  const badge = badgeFor(state);
  return (
    <p className="badge" data-tone={badge.tone} role="status" aria-live="polite">
      <span className="badge-dot" aria-hidden="true" />
      <span>{badge.label}</span>
      {badge.detail ? <span className="badge-detail">{badge.detail}</span> : null}
    </p>
  );
}
