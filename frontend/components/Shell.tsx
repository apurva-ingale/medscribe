"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { api, token } from "@/lib/api";
import type { User } from "@/lib/types";

const Ctx = createContext<User | null>(null);
export const useUser = () => useContext(Ctx)!;

export default function Shell({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  useEffect(() => {
    if (!token()) { router.replace("/login"); return; }
    api<User>("/api/auth/me").then(setUser).catch(() => router.replace("/login"));
  }, [router]);
  if (!user) return <p className="muted pad">Loading…</p>;
  return (
    <Ctx.Provider value={user}>
      <header className="bar">
        <Link href="/" className="brand">MedScribe</Link>
        <nav>
          <Link href="/">Consultations</Link>
          {user.role === "admin" && <Link href="/admin">Users</Link>}
        </nav>
        <span className="muted">{user.name} ({user.role})</span>
        <button className="btn ghost" onClick={() => { localStorage.removeItem("token"); router.replace("/login"); }}>
          Sign out
        </button>
      </header>
      <main className="wrap">{children}</main>
    </Ctx.Provider>
  );
}
