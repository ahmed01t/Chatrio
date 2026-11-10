"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AnalyticsRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/agent");
  }, [router]);

  return (
    <div className="p-8 text-center text-xs text-ink-500">
      Redirecting to AI Agent &amp; Knowledge Base...
    </div>
  );
}
