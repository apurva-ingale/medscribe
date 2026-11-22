"use client";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api, token, WS } from "@/lib/api";
import { Consultation, Note, SECTIONS, SectionKey } from "@/lib/types";

const STAGES = [["preprocessing", "Clean audio"], ["transcribing", "Transcribe"], ["generating", "Draft note"], ["validating", "Check claims"]];

function Detail() {
  const { id } = useParams<{ id: string }>();
  const [c, setC] = useState<Consultation | null>(null);
  const [note, setNote] = useState<Note | null>(null);
  const [stage, setStage] = useState("");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    const d = await api<Consultation>(`/api/consultations/${id}`);
    setC(d); setNote(d.note); setStage(d.stage);
  }, [id]);

  useEffect(() => { load().catch((e) => setErr(e.message)); }, [load]);

  const active = !!c && (c.status === "uploaded" || c.status === "processing");
  useEffect(() => {
    if (!active) return;
    const ws = new WebSocket(`${WS}/ws/consultations/${id}?token=${token()}`);
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.stage) setStage(m.stage);
      if (m.status === "review" || m.status === "failed") load();
      else if (m.transcript) setC((p) => (p ? { ...p, transcript: m.transcript } : p));
    };
    return () => ws.close();
  }, [active, id, load]);

  if (!c) return <p className={err ? "err" : "muted"}>{err || "Loading…"}</p>;

  const editable = c.status === "review";
  const edit = (fn: (n: Note) => Note) => { setNote((n) => (n ? fn(n) : n)); setDirty(true); };
  const flagsFor = (k: SectionKey, i: number) => (dirty ? [] : c.flags.filter((f) => f.section === k && f.index === i));

  async function save() {
    setBusy(true); setErr("");
    try {
      const d = await api<Consultation>(`/api/consultations/${id}/note`, { method: "PUT", body: JSON.stringify(note) });
      setC(d); setNote(d.note); setDirty(false);
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  async function finalize() {
    const n = c!.flags.length;
    if (n && !window.confirm(`${n} item(s) are flagged. Confirm that you have reviewed them and want to finalize?`)) return;
    setBusy(true); setErr("");
    try {
      setC(await api<Consultation>(`/api/consultations/${id}/finalize`, { method: "POST", body: JSON.stringify({ confirm_flags: n > 0 }) }));
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  const copy = () => navigator.clipboard.writeText(
    SECTIONS.filter(([k]) => note![k].length).map(([k, l]) => `${l}\n${note![k].map((i) => `- ${i.text}`).join("\n")}`).join("\n\n"));

  return (
    <>
      <div className="row between">
        <div><h1>{c.patient_label}</h1><span className="muted">{new Date(c.created_at).toLocaleString()} · {c.doctor_name}</span></div>
        <span className={`tag ${c.status}`}>{c.status}</span>
      </div>

      {active && (
        <div className="panel">
          <h2>Processing</h2>
          <div className="steps">
            {STAGES.map(([k, l], i) => {
              const cur = STAGES.findIndex(([s]) => s === stage);
              return <span key={k} className={`step ${i < cur ? "done" : i === cur ? "now" : ""}`}>{l}</span>;
            })}
          </div>
        </div>
      )}
      {c.status === "failed" && <div className="panel err">Processing failed: {c.error}</div>}

      {c.transcript && (
        <details className="panel" open={!note}>
          <summary><strong>Transcript</strong></summary>
          <p className="transcript">{c.transcript}</p>
        </details>
      )}

      {note && (
        <section className="panel">
          <div className="row between">
            <h2>Clinical note</h2>
            <span className="muted">
              {c.status === "finalized" ? `Finalized ${new Date(c.finalized_at!).toLocaleString()}`
                : dirty ? "Unsaved edits — save to re-run checks"
                : c.flags.length ? `${c.flags.length} item(s) need review` : "All checks passed"}
            </span>
          </div>
          {SECTIONS.map(([k, label]) => (
            <div key={k}>
              <h3>{label}</h3>
              {!dirty && c.flags.filter((f) => f.section === k && f.index < 0).map((f, j) => <span key={j} className="reason">{f.reason}</span>)}
              {note[k].length === 0 && <p className="muted">Not discussed</p>}
              {note[k].map((it, i) => {
                const fl = flagsFor(k, i);
                return (
                  <div key={i} className={`note-item ${fl.length ? "flagged" : ""}`}>
                    <div className="row">
                      <textarea rows={Math.max(1, Math.ceil(it.text.length / 80))} value={it.text} disabled={!editable}
                        style={{ flex: 1 }}
                        onChange={(e) => edit((n) => ({ ...n, [k]: n[k].map((x, j) => (j === i ? { ...x, text: e.target.value } : x)) }))} />
                      {editable && <button className="btn danger" onClick={() => edit((n) => ({ ...n, [k]: n[k].filter((_, j) => j !== i) }))}>Remove</button>}
                    </div>
                    {it.source_quote && <small className="quote">“{it.source_quote}”</small>}
                    {fl.map((f, j) => <span key={j} className="reason">⚠ {f.reason}</span>)}
                  </div>
                );
              })}
              {editable && <button className="btn ghost" onClick={() => edit((n) => ({ ...n, [k]: [...n[k], { text: "", source_quote: "" }] }))}>Add item</button>}
            </div>
          ))}
          {err && <p className="err">{err}</p>}
          <div className="row" style={{ marginTop: "1rem" }}>
            {editable && <button className="btn ghost" disabled={!dirty || busy} onClick={save}>Save changes</button>}
            {editable && <button className="btn" disabled={dirty || busy} onClick={finalize}>Finalize note</button>}
            <button className="btn ghost" onClick={copy}>Copy as text</button>
          </div>
        </section>
      )}
    </>
  );
}

export default function Page() { return <Shell><Detail /></Shell>; }
