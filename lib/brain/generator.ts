"use client";

import { Timepoint } from "./types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function requestGeneratedImages(input: {
  prompt: string;
  timepoints?: Timepoint[];
}): Promise<Partial<Record<Timepoint, string>>> {
  if (!BACKEND_URL) {
    throw new Error("NEXT_PUBLIC_BACKEND_URL is not set");
  }
  const res = await fetch(`${BACKEND_URL}/model/generate_images`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: input.prompt,
      timepoints: input.timepoints ?? ["now", "3m", "6m", "12m"],
    }),
  });
  if (!res.ok) {
    throw new Error(`Backend error: ${res.status} ${res.statusText}`);
  }
  const data = (await res.json()) as { images?: Partial<Record<Timepoint, string>> };
  return data.images ?? {};
}


