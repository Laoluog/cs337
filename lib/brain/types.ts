export type Timepoint = "now" | "3m" | "6m" | "12m";

export interface FileMeta {
  name: string;
  size: number;
  type: string;
}

export interface PatientInfo {
  firstName?: string;
  lastName?: string;
  age?: number;
  mrn?: string;
  notes?: string;
}

export interface ImageResult {
  url: string;
  timepoint: Timepoint;
  promptUsed: string;
}

export interface CaseData {
  id: string;
  createdAt: string;
  patient: PatientInfo;
  basePrompt: string;
  generatedPrompt?: string;
  ehrFiles: FileMeta[];
  ctScans: FileMeta[];
  images: Partial<Record<Timepoint, ImageResult>>;
  videoUrl?: string;
}


