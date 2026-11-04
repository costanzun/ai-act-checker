"use client";

import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CiteList, RichText } from "@/components/cite/RichText";
import { useT } from "@/i18n";
import type { Obligation, Role } from "@/lib/types";

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

const CONDITIONAL = /^\s*(only if|required if|solo se|obbligatoria se)/i;
const isConditional = (o: Obligation) => o.priority === "should" && (CONDITIONAL.test(o.summary.en ?? "") || CONDITIONAL.test(o.summary.it ?? ""));

function Group({ title, items }: { title: string; items: Obligation[] }) {
  const { t } = useT();
  const firm = items.filter((o) => !isConditional(o));
  const cond = items.filter(isConditional);
  return (
    <div>
      <h3 className="mt-5 border-b border-border pb-1 text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground first:mt-0">{title}</h3>
      {firm.length > 0 && <ul className="divide-y divide-border">{firm.map((o) => <ObligationItem key={o.id} o={o} />)}</ul>}
      {cond.length > 0 && (
        <div className="mt-2 rounded-md border border-dashed border-border bg-background/50 px-3 opacity-80" data-testid="conditional-group">
          <p className="pt-2 text-xs font-medium text-muted-foreground">{t("obl.conditional")}</p>
          <ul className="divide-y divide-border">{cond.map((o) => <ObligationItem key={o.id} o={o} />)}</ul>
        </div>
      )}
    </div>
  );
}

function group<K extends string>(items: Obligation[], key: (o: Obligation) => K): [K, Obligation[]][] {
  const m = new Map<K, Obligation[]>();
  for (const o of items) m.set(key(o), [...(m.get(key(o)) ?? []), o]);
  return [...m.entries()];
}

function roleHeading(group: Obligation["role"], userRole: Role, t: ReturnType<typeof useT>["t"]): string {
  if (group === "both") return t("obl.role.shared");
  const noun = t(group === "provider" ? "obl.role.provider" : "obl.role.deployer");
  const mine = userRole === group || userRole === "both";
  return mine ? t("obl.role.you", { role: noun }) : t("obl.role.other", { role: noun });
}

export function ObligationsTabs({ obligations, role }: { obligations: Obligation[]; role: Role }) {
  const { t } = useT();
  const must = obligations.filter((o) => o.priority === "must").length;
  const mineFirst = (g: Obligation["role"]) => (g === role || role === "both" ? 0 : g === "both" ? 2 : 1);
  const catLabel = (c: string) => c.charAt(0).toUpperCase() + c.slice(1);
  return (
    <section aria-labelledby="obligations-heading">
      <h2 id="obligations-heading" className="font-heading text-2xl font-medium">{t("result.obligations")}</h2>
      {obligations.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">{t("result.obligations.empty")}</p>
      ) : (
        <>
          <p className="mt-2 text-sm text-muted-foreground" data-testid="obligations-count">
            {t(obligations.length === 1 ? "result.obligations.count.one" : "result.obligations.count", { n: obligations.length, must, should: obligations.length - must })}
          </p>
          <Tabs defaultValue="category" className="mt-4 print:hidden">
            <TabsList>
              <TabsTrigger value="category">{t("result.obligations.byCategory")}</TabsTrigger>
              <TabsTrigger value="role">{t("result.obligations.byRole")}</TabsTrigger>
            </TabsList>
            <TabsContent value="category" className="rounded-lg border border-border bg-card p-4 sm:p-5">
              {group(obligations, (o) => o.category).map(([c, items]) => <Group key={c} title={catLabel(c)} items={items} />)}
            </TabsContent>
            <TabsContent value="role" className="rounded-lg border border-border bg-card p-4 sm:p-5">
              {group(obligations, (o) => o.role).sort((a, b) => mineFirst(a[0]) - mineFirst(b[0])).map(([r, items]) => <Group key={r} title={roleHeading(r, role, t)} items={items} />)}
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
