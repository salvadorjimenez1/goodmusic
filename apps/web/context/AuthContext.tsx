"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { apiFetch } from "../lib/api";

type User = {
  id: number;
  username: string;
};

type AuthContextType = {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  async function login(username: string, password: string) {
    const res = await fetch("http://localhost:8000/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }),
    });
    
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      if (data.detail === "Email not verified") {
        throw new Error("Please verify your email before logging in.");
      }
      throw new Error("Invalid username or password");
    }

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    // fetch /me for user info
    const me = await apiFetch("/me");
    setUser(me);
  }

async function register(username: string, email: string, password: string, confirmPassword: string) {
  const res = await fetch("http://localhost:8000/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password, confirm_password: confirmPassword }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data;

  return data;
}

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}