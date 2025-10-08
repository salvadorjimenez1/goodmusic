"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const searchParams = useSearchParams();
  const registered = searchParams.get("registered");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      router.push(`/profile/${username}`);
    } catch (err : any) {
      const msg =
        err?.message ||
        err?.detail ||
        "Your credentials don't match. It's probably attributable to human error.";
      setError(String(msg));
      // optional: auto-dismiss after 30s
      window.setTimeout(() => setError(null), 30000);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto mt-10 text-white">
      <h1 className="text-2xl mb-4">Login</h1>
      
      {registered && (
        <p className="text-green-600 font-medium">
          Registration successful! Please verify your email before logging in.
        </p>
      )}

        {/* Inline error banner */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="mb-4 rounded shadow-sm bg-orange-600 text-white px-4 py-3"
        >
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 opacity-90 mt-[2px]"
              viewBox="0 0 20 20"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.72-1.36 3.485 0l6.518 11.59A1.75 1.75 0 0 1 17.518 17H2.482a1.75 1.75 0 0 1-1.742-2.311L8.257 3.1zM11 13a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm-.25-6a.75.75 0 0 0-1.5 0v3a.75.75 0 0 0 1.5 0v-3z"
                clipRule="evenodd"
              />
            </svg>

            <div className="flex-1">
              <p className="font-medium leading-tight">{error}</p>
            </div>

            <button
              onClick={() => setError(null)}
              aria-label="Dismiss error"
              className="ml-3 text-white opacity-90 hover:opacity-100"
            >
              ✕
            </button>
          </div>
        </div>
      )}



      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          className="w-full p-2 border rounded"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full p-2 border rounded"
        />
        <button className="px-4 py-2 bg-indigo-600 rounded text-white w-full">
          Login
        </button>
      </form>
    </div>
  );
}