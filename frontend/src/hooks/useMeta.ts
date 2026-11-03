"use client";

import { useEffect, useState } from "react";
import { FALLBACK_META, getMeta } from "@/lib/api";
import type { Meta } from "@/lib/types";

/** Fetches /api/meta once per page load; `meta` is null until loaded (or when unavailable). */
export function useMeta() {
  const [meta, setMeta] = useState<Meta | null>(null);
  useEffect(() => {
    let alive = true;
    getMeta().then((m) => alive && setMeta(m)).catch(() => undefined);
    return () => { alive = false; };
  }, []);
  return { meta, lawAsOf: meta?.law_as_of ?? FALLBACK_META.law_as_of, checkedAt: meta?.checked_at ?? FALLBACK_META.checked_at };
}
