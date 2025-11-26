"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listCasesSupabase } from "@/lib/brain/db";

export function HomeLanding() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    (async () => {
      try {
        const list = await listCasesSupabase();
        setCount(list.length);
      } catch {
        setCount(0);
      }
    })();
  }, []);

  return (
    <div className="flex flex-col items-center gap-10">
      <h1 className="text-3xl md:text-4xl font-bold text-center">
        Brain Imaging Studio
      </h1>

      <div className="relative w-40 h-40 md:w-56 md:h-56">
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 blur-2xl opacity-40" />
        <div className="relative w-full h-full rounded-full bg-background border flex items-center justify-center text-6xl md:text-7xl animate-spin-slow">
          <span role="img" aria-label="brain">🧠</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
        <Link
          href="/protected/brain/cases"
          className="rounded-lg border p-6 hover:shadow transition flex flex-col gap-3"
        >
          <div className="text-sm uppercase tracking-wide text-muted-foreground">
            Patients & Cases
          </div>
          <div className="text-xl font-semibold">Browse Existing</div>
          <div className="text-sm text-muted-foreground">
            {count} case{count === 1 ? "" : "s"} found
          </div>
        </Link>
        <Link
          href="/protected/brain/input"
          className="rounded-lg border p-6 hover:shadow transition flex flex-col gap-3"
        >
          <div className="text-sm uppercase tracking-wide text-muted-foreground">
            New Input
          </div>
          <div className="text-xl font-semibold">Create New Case</div>
          <div className="text-sm text-muted-foreground">
            Upload EHR + CT, set context, and generate images
          </div>
        </Link>
      </div>
    </div>
  );
}


