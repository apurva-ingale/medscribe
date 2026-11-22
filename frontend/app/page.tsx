"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";
import Shell, { useUser } from "@/components/Shell";
import { api } from "@/lib/api";
import type { Consultation } from "@/lib/types";

function Dashboard() {
  const user = useUser();
  const router = useRouter();
  const [items, setItems] = useState<Consultation[]>([]);
  const [label, setLabel] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const rec = useRef<MediaRecorder | null>(null);

  useEffect(() => { api<Consultation[]>("/api/consultations").then(setItems).catch((e) => setErr(e.message)); }, []);

  async function toggleRecord() {
    if (recording) { rec.current?.stop(); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      mr.ondataavailable = (e) => chunks.push(e.data);
      mr.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        setFile(new File(chunks, `recording-${Date.now()}.webm`, { type: mr.mimeType || "audio/webm" }));
        setRecording(false);
      };
      mr.start(); rec.current = mr; setRecording(true);
    } catch { setErr("Microphone access was denied. Upload a file instead."); }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true); setErr("");
    try {
      const fd = new FormData();
      fd.append("patient_label", label);
      fd.append("audio", file);
      const c = await api<Consultation>("/api/consultations", { method: "POST", body: fd });
      router.push(`/consultations/${c.id}`);
    } catch (e) { setErr((e as Error).message); setBusy(false); }
  }

  return (
    <>
      <form className="panel" onSubmit={submit}>
        <h2>New consultation</h2>
        <div className="row">
          <input placeholder="Patient name or ID" value={label} onChange={(e) => setLabel(e.target.value)} required />
          <input type="file" accept="audio/*,video/webm,video/mp4" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button type="button" className={recording ? "btn danger" : "btn ghost"} onClick={toggleRecord}>
            {recording ? "Stop recording" : "Record"}
          </button>
          <button className="btn" disabled={!file || busy || recording}>{busy ? "Uploading…" : "Generate note"}</button>
        </div>
        {file && <p className="muted">Ready: {file.name}</p>}
        {err && <p className="err">{err}</p>}
      </form>
      <section className="panel list">
        <h2>{user.role === "admin" ? "All consultations" : "Your consultations"}</h2>
        {items.length === 0 && <p className="muted">No consultations yet. Record or upload audio above.</p>}
        {items.map((c) => (
          <Link key={c.id} href={`/consultations/${c.id}`} className="item">
            <span>
              <strong>{c.patient_label}</strong>
              <span className="muted"> · {new Date(c.created_at).toLocaleString()}{user.role === "admin" && ` · ${c.doctor_name}`}</span>
            </span>
            <span className={`tag ${c.status}`}>{c.status}</span>
          </Link>
        ))}
      </section>
    </>
  );
}

export default function Page() { return <Shell><Dashboard /></Shell>; }
