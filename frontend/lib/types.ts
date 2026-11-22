export const SECTIONS = [
  ["chief_complaint", "Chief complaint"],
  ["history_of_present_illness", "History of present illness"],
  ["symptoms", "Symptoms"],
  ["past_medical_history", "Past medical history"],
  ["medications", "Medications"],
  ["allergies", "Allergies"],
  ["examination_findings", "Examination findings"],
  ["assessment", "Assessment"],
  ["plan", "Plan"],
  ["follow_up", "Follow-up"],
] as const;

export type SectionKey = (typeof SECTIONS)[number][0];
export type Item = { text: string; source_quote: string };
export type Note = Record<SectionKey, Item[]>;
export type Flag = { section: SectionKey; index: number; reason: string };
export type User = { id: number; email: string; name: string; role: "doctor" | "admin" };
export type Consultation = {
  id: string; patient_label: string; status: "uploaded" | "processing" | "review" | "finalized" | "failed";
  stage: string; transcript: string | null; note: Note | null; flags: Flag[]; error: string | null;
  created_at: string; finalized_at: string | null; doctor_name: string;
};
