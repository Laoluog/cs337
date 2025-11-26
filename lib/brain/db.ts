"use client";

import { createClient } from "@/lib/supabase/client";
import { CaseData, ImageResult, PatientInfo, Timepoint } from "./types";

export type CaseRow = {
  id: string;
  created_at: string;
  user_id: string | null;
  patient_first_name: string | null;
  patient_last_name: string | null;
  patient_age: number | null;
  patient_mrn: string | null;
  patient_notes: string | null;
  base_prompt: string | null;
  ehr_files: Array<{ name: string; size: number; type: string; path?: string }> | null;
  ct_scans: Array<{ name: string; size: number; type: string; path?: string }> | null;
  images: Partial<Record<Timepoint, ImageResult>> | null;
  video_url: string | null;
};

function toCaseData(row: CaseRow): CaseData {
  return {
    id: row.id,
    createdAt: row.created_at,
    patient: {
      firstName: row.patient_first_name ?? undefined,
      lastName: row.patient_last_name ?? undefined,
      age: row.patient_age ?? undefined,
      mrn: row.patient_mrn ?? undefined,
      notes: row.patient_notes ?? undefined,
    },
    basePrompt: row.base_prompt ?? "",
    ehrFiles: row.ehr_files ?? [],
    ctScans: row.ct_scans ?? [],
    images: row.images ?? {},
    videoUrl: row.video_url ?? undefined,
  };
}

function fileMeta(file: File) {
  return { name: file.name, size: file.size, type: file.type };
}

function placeholder(seed: string, timepoint: Timepoint): string {
  return `https://picsum.photos/seed/${encodeURIComponent(`${seed}-${timepoint}`)}/960/720`;
}

export async function listCasesSupabase(): Promise<CaseData[]> {
  const supabase = createClient();
  const { data, error } = await supabase
    .from("cases")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data as CaseRow[]).map(toCaseData);
}

export async function getCaseSupabase(caseId: string): Promise<CaseData> {
  const supabase = createClient();
  const { data, error } = await supabase
    .from("cases")
    .select("*")
    .eq("id", caseId)
    .single();
  if (error) throw error;
  return toCaseData(data as CaseRow);
}

export async function createCaseSupabase(input: {
  patient: PatientInfo;
  basePrompt: string;
  ehrFiles: File[];
  ctScans: File[];
}): Promise<CaseData> {
  const supabase = createClient();
  // TODO: upload files to Supabase Storage and fill "path" fields below
  const insert = {
    patient_first_name: input.patient.firstName ?? null,
    patient_last_name: input.patient.lastName ?? null,
    patient_age: input.patient.age ?? null,
    patient_mrn: input.patient.mrn ?? null,
    patient_notes: input.patient.notes ?? null,
    base_prompt: input.basePrompt,
    ehr_files: input.ehrFiles.map(fileMeta),
    ct_scans: input.ctScans.map(fileMeta),
    images: {}, // initially empty
  };
  const { data, error } = await supabase
    .from("cases")
    .insert(insert)
    .select("*")
    .single();
  if (error) throw error;
  return toCaseData(data as CaseRow);
}

export async function generateImagesSupabase(params: {
  caseId: string;
  additionalPrompt?: string;
  timepoints?: Timepoint[];
}): Promise<CaseData> {
  const supabase = createClient();
  const current = await getCaseSupabase(params.caseId);
  const tps = params.timepoints ?? ["now", "3m", "6m", "12m"];
  const nextImages: Partial<Record<Timepoint, ImageResult>> = { ...current.images };
  for (const tp of tps) {
    nextImages[tp] = {
      url: placeholder(current.id, tp),
      timepoint: tp,
      promptUsed: params.additionalPrompt
        ? `${current.basePrompt} ${params.additionalPrompt}`.trim()
        : current.basePrompt,
    };
  }
  const { data, error } = await supabase
    .from("cases")
    .update({ images: nextImages })
    .eq("id", params.caseId)
    .select("*")
    .single();
  if (error) throw error;
  return toCaseData(data as CaseRow);
}


