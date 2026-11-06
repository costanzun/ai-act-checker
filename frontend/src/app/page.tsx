import { Suspense } from "react";
import { Checker } from "@/components/checker/Checker";

export default function HomePage() {
  return (
    <Suspense>
      <Checker />
    </Suspense>
  );
}
