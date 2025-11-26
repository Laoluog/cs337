"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { PatientInfo } from "@/lib/brain/types";
import { createCaseSupabase } from "@/lib/brain/db";
import { requestModelPrompt } from "@/lib/brain/model";
import { requestGeneratedImages } from "@/lib/brain/generator";
import { updateCaseImagesSupabase } from "@/lib/brain/db";
import type { Timepoint } from "@/lib/brain/types";

export default function BrainInputPage() {
  const router = useRouter();
  const [patient, setPatient] = useState<PatientInfo>({});
  const [basePrompt, setBasePrompt] = useState("");
  const [ehrFiles, setEhrFiles] = useState<File[]>([]);
  const [ctFiles, setCtFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      // Ask backend model for a refined/generative prompt (optional; falls back to user prompt)
      let generatedPrompt: string | null = null;
      try {
        generatedPrompt = await requestModelPrompt({
          patient,
          basePrompt,
          ehrFiles,
          ctScans: ctFiles,
        });
      } catch {
        // ignore backend failures, proceed with user-provided basePrompt
      }

      const created = await createCaseSupabase({
        patient,
        basePrompt,
        generatedPrompt: generatedPrompt ?? null,
        ehrFiles,
        ctScans: ctFiles,
      });

      // Generate images from backend using generatedPrompt (fallback to basePrompt)
      const finalPrompt = generatedPrompt ?? basePrompt;
      try {
        const urls = await requestGeneratedImages({ prompt: finalPrompt });
        const tps: Timepoint[] = ["now", "3m", "6m", "12m"];
        const images = tps.reduce((acc, tp) => {
          const url = urls[tp];
          if (url) {
            acc[tp] = {
              url,
              timepoint: tp,
              promptUsed: finalPrompt,
            };
          }
          return acc;
        }, {} as Record<Timepoint, { url: string; timepoint: Timepoint; promptUsed: string }>);
        if (Object.keys(images).length > 0) {
          await updateCaseImagesSupabase(created.id, images);
        }
      } catch {
        // If generation fails, continue to case page; user can retry there
      }

      router.push(`/protected/brain/${created.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Create Case</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="firstName">First name</Label>
            <Input
              id="firstName"
              value={patient.firstName ?? ""}
              onChange={(e) => setPatient((p) => ({ ...p, firstName: e.target.value }))}
              placeholder="Jane"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="lastName">Last name</Label>
            <Input
              id="lastName"
              value={patient.lastName ?? ""}
              onChange={(e) => setPatient((p) => ({ ...p, lastName: e.target.value }))}
              placeholder="Doe"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="age">Age</Label>
            <Input
              id="age"
              type="number"
              min={0}
              value={patient.age?.toString() ?? ""}
              onChange={(e) =>
                setPatient((p) => ({ ...p, age: e.target.value ? Number(e.target.value) : undefined }))
              }
              placeholder="55"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="mrn">MRN (optional)</Label>
            <Input
              id="mrn"
              value={patient.mrn ?? ""}
              onChange={(e) => setPatient((p) => ({ ...p, mrn: e.target.value }))}
              placeholder="123456"
            />
          </div>
          <div className="md:col-span-2 flex flex-col gap-2">
            <Label htmlFor="notes">Clinical notes (optional)</Label>
            <Input
              id="notes"
              value={patient.notes ?? ""}
              onChange={(e) => setPatient((p) => ({ ...p, notes: e.target.value }))}
              placeholder="Brief summary or relevant conditions"
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="basePrompt">Base prompt</Label>
          <Input
            id="basePrompt"
            value={basePrompt}
            onChange={(e) => setBasePrompt(e.target.value)}
            placeholder="Describe case context to guide image generation"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
            <Label htmlFor="ehrFiles">EHR files (PDF/JSON/TXT)</Label>
            <Input
              id="ehrFiles"
              type="file"
              multiple
              accept=".pdf,.json,.txt,.csv"
              onChange={(e) => setEhrFiles(Array.from(e.target.files ?? []))}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="ctFiles">CT scans (DICOM/Images)</Label>
            <Input
              id="ctFiles"
              type="file"
              multiple
              accept=".dcm,.dicom,.png,.jpg,.jpeg"
              onChange={(e) => setCtFiles(Array.from(e.target.files ?? []))}
            />
          </div>
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <div>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Creating..." : "Create case"}
          </Button>
        </div>
      </form>
    </div>
  );
}


