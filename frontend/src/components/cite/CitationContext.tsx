"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { CitationPanel } from "./CitationPanel";

interface Ctx { openCite: (id: string) => void; closeCite: () => void }
const CiteCtx = createContext<Ctx>({ openCite: () => {}, closeCite: () => {} });

const HASH_RE = /^#cite=(.+)$/;

function readHash(): string | null {
  const m = HASH_RE.exec(decodeURIComponent(window.location.hash));
  return m ? m[1] : null;
}

/** Owns the single CitationPanel and syncs it with `#cite=<id>` so links are shareable. */
export function CitationProvider({ children }: { children: ReactNode }) {
  const [id, setId] = useState<string | null>(null);

  useEffect(() => {
    const sync = () => setId(readHash());
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  const openCite = useCallback((next: string) => {
    setId(next);
    const url = new URL(window.location.href);
    url.hash = `cite=${next}`;
    window.history.replaceState(window.history.state, "", url.toString());
  }, []);

  const closeCite = useCallback(() => {
    setId(null);
    const url = new URL(window.location.href);
    url.hash = "";
    window.history.replaceState(window.history.state, "", url.pathname + url.search);
  }, []);

  const value = useMemo(() => ({ openCite, closeCite }), [openCite, closeCite]);
  return (
    <CiteCtx.Provider value={value}>
      {children}
      <CitationPanel id={id} onClose={closeCite} />
    </CiteCtx.Provider>
  );
}

export const useCite = () => useContext(CiteCtx);
