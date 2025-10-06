"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [errors, setErrors] = useState<{
    username?: string;
    password?: string;
    confirm_password?: string;
  }>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({}); // reset

    try {
      await register(username, password, confirmPassword);
      router.push(`/profile/${username}`);
    } catch (err: any) {
  const newErrors: { username?: string; password?: string; confirm_password?: string } = {};

  if (Array.isArray(err?.detail)) {
    for (const issue of err.detail) {
      if (issue.loc?.includes("username")) {
        newErrors.username = issue.msg;
      }
      if (issue.loc?.includes("password") && !issue.loc.includes("confirm_password")) {
        newErrors.password = issue.msg;
      }
      if (issue.loc?.includes("confirm_password")) {
        newErrors.confirm_password = issue.msg;
      }
    }
  } else if (typeof err?.detail === "string") {
    // fallback string error
    if (err.detail.toLowerCase().includes("username")) {
      newErrors.username = err.detail;
    } else if (err.detail.toLowerCase().includes("password")) {
      newErrors.password = err.detail;
    } else if (err.detail.toLowerCase().includes("confirm")) {
      newErrors.confirm_password = err.detail;
    }
  } else {
    newErrors.username = "Registration failed";
  }

  setErrors(newErrors);
}
  }

  return (
    <div className="max-w-md mx-auto mt-10 text-white">
      <h1 className="text-2xl mb-4">Register</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Username */}
        <div>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            className={`w-full p-2 rounded bg-gray-700 text-white border ${
              errors.username ? "border-red-500" : "border-gray-600"
            }`}
          />
          {errors.username && (
            <p className="mt-1 text-sm text-red-400">{errors.username}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className={`w-full p-2 rounded bg-gray-700 text-white border ${
              errors.password ? "border-red-500" : "border-gray-600"
            }`}
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-400">{errors.password}</p>
          )}
        </div>

        {/* Confirm Password */}
        <div>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm Password"
            className={`w-full p-2 rounded bg-gray-700 text-white border ${
              errors.confirm_password ? "border-red-500" : "border-gray-600"
            }`}
          />
          {errors.confirm_password && (
            <p className="mt-1 text-sm text-red-400">
              {errors.confirm_password}
            </p>
          )}
        </div>

        <button
          type="submit"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-white w-full"
        >
          Register
        </button>
      </form>
    </div>
  );
}