"use client";

import { Fragment } from "react";
import { Cite } from "./Cite";
import { CITE_TOKEN } from "@/lib/cite";

/** Renders plain text with [[art:6.2]] tokens converted to <Cite> chips. */
export function RichText({ text }: { text: string }) {
  const out: React.ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(CITE_TOKEN)) {
    const at = m.index ?? 0;
    if (at > last) out.push(<Fragment key={`t${at}`}>{text.slice(last, at)}</Fragment>);
    out.push(<Cite key={`c${at}`} id={m[1]} />);
    last = at + m[0].length;
  }
  if (last < text.length) out.push(<Fragment key="tail">{text.slice(last)}</Fragment>);
  return <>{out}</>;
}

/** A row of citation chips for a list of IDs. */
export function CiteList({ ids }: { ids: string[] }) {
  if (!ids.length) return null;
  return (
    <span className="inline-flex flex-wrap items-center gap-y-1">
      {ids.map((id) => <Cite key={id} id={id} />)}
    </span>
  );
}
