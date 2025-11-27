"use client";

const BACKEND_URL = "http://127.0.0.1:5000/"

export async function requestVeoVideo(input: {
  imageUrl: string;
  prompt: string;
  seconds?: number;
}): Promise<string> {
  if (!BACKEND_URL) {
    throw new Error("NEXT_PUBLIC_BACKEND_URL is not set");
  }
  const res = await fetch(`${BACKEND_URL}/model/generate_video`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_url: input.imageUrl,
      prompt: input.prompt,
      seconds: input.seconds ?? 7,
    }),
  });
  if (!res.ok) {
    throw new Error(`Backend error: ${res.status} ${res.statusText}`);
  }
  const data = (await res.json()) as { video_url?: string };
  if (!data.video_url) {
    throw new Error("No video_url in response");
  }
  return data.video_url;
}


