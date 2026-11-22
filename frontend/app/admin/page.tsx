"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import Shell, { useUser } from "@/components/Shell";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";

function Admin() {
  const me = useUser();
  const [users, setUsers] = useState<User[]>([]);
  const [f, setF] = useState({ name: "", email: "", password: "", role: "doctor" });
  const [err, setErr] = useState("");

  const load = useCallback(() => api<User[]>("/api/auth/users").then(setUsers).catch((e) => setErr(e.message)), []);
  useEffect(() => { if (me.role === "admin") load(); }, [me.role, load]);

  if (me.role !== "admin") return <p className="err">Admins only.</p>;

  async function add(e: FormEvent) {
    e.preventDefault(); setErr("");
    try {
      await api("/api/auth/users", { method: "POST", body: JSON.stringify(f) });
      setF({ name: "", email: "", password: "", role: "doctor" }); load();
    } catch (e) { setErr((e as Error).message); }
  }

  return (
    <>
      <form className="panel" onSubmit={add}>
        <h2>Add user</h2>
        <div className="row">
          <input placeholder="Name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required />
          <input type="email" placeholder="Email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required />
          <input type="password" placeholder="Password (8+ characters)" minLength={8} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required />
          <select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option value="doctor">Doctor</option><option value="admin">Admin</option></select>
          <button className="btn">Add user</button>
        </div>
        {err && <p className="err">{err}</p>}
      </form>
      <section className="panel list">
        <h2>Users</h2>
        {users.map((u) => (
          <div key={u.id} className="item"><span><strong>{u.name}</strong> <span className="muted">{u.email}</span></span><span className="tag">{u.role}</span></div>
        ))}
      </section>
    </>
  );
}

export default function Page() { return <Shell><Admin /></Shell>; }
