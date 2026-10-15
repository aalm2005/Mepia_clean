export type ChatEvidence = {
  audit_result_id: string; node_id: string; date: string; source_s3_result_id: string | null;
};
export type ChatAnswerPart = {
  kind: string; status: string; message: string; data: Record<string, unknown>;
  evidence: ChatEvidence[]; missing_data: string[]; generation_status: "validated" | "fallback";
  claims: { text: string; sources: { path: string; label: string }[] }[];
};
export type ChatAnswer = {
  business_id: string; resolved_date: string | null; calculation_allowed: false; parts: ChatAnswerPart[];
};
export type ChatTurn = { question: string; answer: ChatAnswer };
