import { redirect } from "next/navigation";

/** Old links (/assess?id=…, ?example=…, ?q=…) now land on the single-page checker. */
export default async function AssessPage({ searchParams }: PageProps<"/assess">) {
  const sp = await searchParams;
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(sp)) if (typeof v === "string") qs.set(k, v);
  redirect(qs.size ? `/?${qs.toString()}` : "/");
}
