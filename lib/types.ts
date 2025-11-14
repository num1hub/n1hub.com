export type JobState = "pending" | "processing" | "succeeded" | "failed";

export interface Job {
  id: string;
  code: number;
  stage: string;
  state: JobState;
  progress: number;
  created_at: string;
  updated_at: string;
  error?: {
    code: number;
    stage: string;
    issues: Array<{ path: string; message: string }>;
  } | null;
  capsule_id?: string;
}

export interface CapsuleCorePayload {
  content_type: string;
  content: string;
  truncation_note: string | null;
}

export interface CapsuleMetadata {
  capsule_id: string;
  version: string;
  status: string;
  author: string;
  created_at: string;
  language: string;
  source: {
    type: string;
    uri: string | null;
  };
  tags: string[];
  length: {
    chars: number;
    tokens_est: number;
  };
  semantic_hash: string;
}

export interface CapsuleNeuroConcentrate {
  summary: string;
  keywords: string[];
  entities: Array<{ type: string; name: string }>;
  claims: string[];
  insights: string[];
  questions: string[];
  archetypes: string[];
  symbols: string[];
  emotional_charge: number;
  vector_hint: string[];
  semantic_hash: string;
}

export interface CapsuleLink {
  rel:
    | "supports"
    | "contradicts"
    | "extends"
    | "duplicates"
    | "references"
    | "depends_on"
    | "derived_from";
  target_capsule_id: string;
  reason: string;
  confidence: number;
}

export interface CapsuleRecursive {
  links: CapsuleLink[];
  actions: Array<{ name: string; intent: string; params: Record<string, unknown>; hitl_required: boolean }>;
  prompts: Array<{ title: string; prompt: string }>;
  confidence: number;
}

export interface Capsule {
  include_in_rag: boolean;
  metadata: CapsuleMetadata;
  core_payload: CapsuleCorePayload;
  neuro_concentrate: CapsuleNeuroConcentrate;
  recursive: CapsuleRecursive;
}

export interface ChatRequestBody {
  query: string;
  scope: string[];
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  metrics: Record<string, number>;
}

export interface ObservabilitySummary {
  name: string;
  status: "ok" | "warning" | "error";
  details: string;
  metrics: Record<string, number>;
}
