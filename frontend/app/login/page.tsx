"use client";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { API } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      const r = await fetch(`${API}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? "Sign-in failed");
      localStorage.setItem("token", (await r.json()).access_token);
      router.replace("/");
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  return (
    <form className="panel login" onSubmit={submit}>
      <h1>Sign in to MedScribe</h1>
      <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      {err && <span className="err">{err}</span>}
      <button className="btn" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
    </form>
  );
}
