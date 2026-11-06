"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useT } from "@/i18n";
import { citeLabel, fetchLawCached } from "@/lib/cite";
import type { LawResponse } from "@/lib/types";
import { ProvisionBody } from "./ProvisionBody";

export function LawPage() {
  const params = useParams<{ id: string }>();
  const id = decodeURIComponent(params.id);
  const { t, lang } = useT();
  const [res, setRes] = useState<{ key: string; data: LawResponse | null }|null>(null);
  const key = `${lang}:${id}`;
  useEffect(() => {
    let alive = true;
    fetchLawCached(id, lang).then((data) => alive && setRes({ key, data })).catch(() => alive && setRes({ key, data: null }));
    return () => { alive = false; };
  }, [id, lang, key]);
  const cur = res && res.key === key ? res : null;

  return (
    <article className="mx-auto max-w-3xl py-8 sm:py-12">
      <Link href="/" className="pill pill-secondary h-10 px-4 text-[13.5px]"><ArrowLeft className="size-4" aria-hidden /> {t("law.back")}</Link>
      <h1 className="display mt-4 text-[44px] sm:text-[60px]">{cur?.data?.provision.label ?? citeLabel(id, lang)}</h1>
      <div className="panel mt-5 p-5 sm:p-6">
        {!cur && <div className="space-y-3"><Skeleton className="h-4 w-1/2" /><Skeleton className="h-32 w-full" /></div>}
        {cur && !cur.data && <p role="alert" className="text-muted-foreground">{t("law.notFound")}</p>}
        {cur?.data && <ProvisionBody data={cur.data} asPage />}
      </div>
    </article>
  );
}
