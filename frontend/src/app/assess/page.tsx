"use client";

import { useEffect } from "react";

/** Old links (/assess?id=…, ?example=…, ?q=…) now land on the single-page checker. */
export default function AssessPage() {
  useEffect(() => {
    window.location.replace(`/${window.location.search}${window.location.hash}`);
  }, []);
  return null;
}
