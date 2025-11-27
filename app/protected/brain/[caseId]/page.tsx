"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { CaseData, Timepoint } from "@/lib/brain/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { getCaseSupabase, generateImagesSupabase } from "@/lib/brain/db";
import { requestVeoVideo } from "@/lib/brain/video";

const ALL_TPS: Timepoint[] = ["now", "3m", "6m", "12m"];

export default function BrainCaseOutputPage() {
  const params = useParams<{ caseId: string }>();
  const caseId = params.caseId;
  const [data, setData] = useState<CaseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [selected, setSelected] = useState<Record<Timepoint, boolean>>({
    now: true,
    "3m": true,
    "6m": true,
    "12m": true,
  });
  const [viewerUrl, setViewerUrl] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoLoading, setVideoLoading] = useState<Record<Timepoint, boolean>>({
    now: false,
    "3m": false,
    "6m": false,
    "12m": false,
  });

  const anySelected = useMemo(
    () => ALL_TPS.some((tp) => selected[tp]),
    [selected]
  );

  useEffect(() => {
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const found = await getCaseSupabase(caseId);
        setData(found);
      } catch (e) {
        setError("Case not found");
      } finally {
        setLoading(false);
      }
    })();
  }, [caseId]);

  const onGenerate = () => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const updated = await generateImagesSupabase({ caseId });
        setData(updated);
      } catch {
        setError("Failed to generate images");
      } finally {
        setLoading(false);
      }
    })();
  };

  const onReprompt = () => {
    if (!editText.trim()) return;
    const tps = ALL_TPS.filter((tp) => selected[tp]);
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const updated = await generateImagesSupabase({
          caseId,
          additionalPrompt: editText.trim(),
          timepoints: tps,
        });
        setData(updated);
        setEditText("");
      } catch {
        setError("Failed to reprompt images");
      } finally {
        setLoading(false);
      }
    })();
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">
        Case: {data?.patient?.firstName ?? ""} {data?.patient?.lastName ?? ""} - {data?.patient?.mrn ?? ""}
      </h1>
      {loading ? <div className="text-sm text-muted-foreground">Loading...</div> : null}
      {error ? <div className="text-sm text-red-600">{error}</div> : null}

      {data ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {ALL_TPS.map((tp) => {
              const img = data.images[tp];
              return (
                <div key={tp} className="rounded border p-3">
                  <div className="font-medium mb-2">
                    {tp === "now" ? "Current" : tp.toUpperCase()}
                  </div>
                  <div className="aspect-video rounded overflow-hidden bg-muted/40 flex items-center justify-center">
                    {img ? (
                      /* Using <img> to avoid external image config */
                      <img
                        src={img.url}
                        alt={`${tp} brain image`}
                        className="w-full h-full object-cover cursor-zoom-in"
                        onClick={() => setViewerUrl(img.url)}
                      />
                    ) : (
                      <span className="text-sm text-muted-foreground">No image yet</span>
                    )}
                  </div>
                  <div className="mt-2 flex items-center gap-3">
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={!img || videoLoading[tp]}
                      onClick={async () => {
                        if (!img || !data) return;
                        setVideoLoading((s) => ({ ...s, [tp]: true }));
                        try {
                          const prompt =
                            img.promptUsed || data.generatedPrompt || data.basePrompt || "";
                          const url = await requestVeoVideo({
                            imageUrl: img.url,
                            prompt,
                            seconds: 7,
                          });
                          setVideoUrl(url);
                        } catch {
                          // ignore for now
                        } finally {
                          setVideoLoading((s) => ({ ...s, [tp]: false }));
                        }
                      }}
                    >
                      {videoLoading[tp] ? "Generating video..." : "Generate Video"}
                    </Button>
                    {videoUrl ? (
                      <a className="text-sm underline" href={videoUrl} target="_blank" rel="noreferrer">
                        Open video
                      </a>
                    ) : null}
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground line-clamp-2">
                    {img?.promptUsed ? `Prompt: ${img.promptUsed}` : "—"}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex gap-3 flex-wrap">
            <Button onClick={onGenerate} disabled={loading}>
              {loading ? "Working..." : "Generate Images"}
            </Button>
          </div>

          <div className="rounded border p-4 flex flex-col gap-4">
            <div className="font-medium">Edit and Reprompt</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <Input
                  placeholder="Describe treatments or changes to guide regeneration"
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-3">
                {ALL_TPS.map((tp) => (
                  <label key={tp} className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={selected[tp]}
                      onCheckedChange={(checked) =>
                        setSelected((s) => ({ ...s, [tp]: Boolean(checked) }))
                      }
                    />
                    {tp === "now" ? "Now" : tp.toUpperCase()}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <Button onClick={onReprompt} disabled={!editText.trim() || !anySelected || loading}>
                {loading ? "Working..." : "Reprompt Selected"}
              </Button>
            </div>
          </div>
        </>
      ) : null}

      {viewerUrl ? (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setViewerUrl(null)}
        >
          <div className="relative w-full h-full max-w-5xl max-h-[90vh] flex items-center justify-center">
            <img
              src={viewerUrl}
              alt="Expanded brain image"
              className="max-h-[90vh] max-w-[90vw] object-contain rounded shadow-lg"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              type="button"
              className="absolute top-2 right-2 rounded px-3 py-1 bg-white/90 text-black text-sm hover:bg-white"
              onClick={() => setViewerUrl(null)}
            >
              Close
            </button>
          </div>
        </div>
      ) : null}

      {videoUrl ? (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setVideoUrl(null)}
        >
          <div className="relative w-full h-full max-w-5xl max-h-[90vh] flex items-center justify-center">
            <video
              src={videoUrl}
              controls
              autoPlay
              className="max-h-[90vh] max-w-[90vw] rounded shadow-lg bg-black"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              type="button"
              className="absolute top-2 right-2 rounded px-3 py-1 bg-white/90 text-black text-sm hover:bg-white"
              onClick={() => setVideoUrl(null)}
            >
              Close
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}


