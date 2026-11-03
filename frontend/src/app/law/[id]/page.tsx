import { Suspense } from "react";
import { LawPage } from "@/components/cite/LawPage";

export default function Page() {
  return (
    <Suspense>
      <LawPage />
    </Suspense>
  );
}
