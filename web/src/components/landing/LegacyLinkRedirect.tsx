"use client";

import { useEffect } from "react";

/** Links shared before the viewer moved to /viewer (`/?target=…`, `/?ra=…`) still open the same view. */
export function LegacyLinkRedirect() {
  useEffect(() => {
    const q = window.location.search;
    if (/[?&](target|ra|dec)=/.test(q)) window.location.replace(`/viewer${q}`);
  }, []);
  return null;
}
