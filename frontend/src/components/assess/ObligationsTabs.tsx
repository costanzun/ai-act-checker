"use client";

import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CiteList, RichText } from "@/components/cite/RichText";
import { useT } from "@/i18n";
import type { Obligation } from "@/lib/types";

function ObligationItem({ o }: { o: Obligation }) {
  const { t, l, formatDate } = useT();
  return (
    <li className="space-y-2 py-4" data-testid="obligation">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="font-medium">{l(o.title)}</h4>
        <Badge variant={o.priority === "must" ? "default" : "secondary"}>{t(o.priority === "must" ? "result.obligations.must" : "result.obligations.should")}</Badge>
        {o.applies_from && <Badge variant="outline" className="font-mono text-[0.7rem]">{t("result.obligations.appliesFrom", { date: formatDate(o.applies_from) })}</Badge>}
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground"><RichText text={l(o.summary)} /></p>
      <CiteList ids={o.citations} />
    </li>
  );
}

function Group({ title, items }: { title: string; items: Obligation[] }) {
  return (
    <div>
      <h3 className="mt-5 border-b border-border pb-1 text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground first:mt-0">{title}</h3>
      <ul className="divide-y divide-border">{items.map((o) => <ObligationItem key={o.id} o={o} />)}</ul>
    </div>
  );
}

function group<K extends string>(items: Obligation[], key: (o: Obligation) => K): [K, Obligation[]][] {
  const m = new Map<K, Obligation[]>();
  for (const o of items) m.set(key(o), [...(m.get(key(o)) ?? []), o]);
  return [...m.entries()];
}

export function ObligationsTabs({ obligations }: { obligations: Obligation[] }) {
  const { t } = useT();
  const catLabel = (c: string) => c.charAt(0).toUpperCase() + c.slice(1);
  return (
    <section aria-labelledby="obligations-heading">
      <h2 id="obligations-heading" className="font-heading text-2xl font-medium">{t("result.obligations")}</h2>
      {obligations.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">{t("result.obligations.empty")}</p>
      ) : (
        <>
          <Tabs defaultValue="category" className="mt-4 print:hidden">
            <TabsList>
              <TabsTrigger value="category">{t("result.obligations.byCategory")}</TabsTrigger>
              <TabsTrigger value="role">{t("result.obligations.byRole")}</TabsTrigger>
            </TabsList>
            <TabsContent value="category" className="rounded-lg border border-border bg-card p-4 sm:p-5">
              {group(obligations, (o) => o.category).map(([c, items]) => <Group key={c} title={catLabel(c)} items={items} />)}
            </TabsContent>
            <TabsContent value="role" className="rounded-lg border border-border bg-card p-4 sm:p-5">
              {group(obligations, (o) => o.role).map(([r, items]) => <Group key={r} title={t(`role.${r}` as const)} items={items} />)}
            </TabsContent>
          </Tabs>
          <div className="mt-4 hidden print:block">
            {group(obligations, (o) => o.category).map(([c, items]) => <Group key={c} title={catLabel(c)} items={items} />)}
          </div>
        </>
      )}
    </section>
  );
}
