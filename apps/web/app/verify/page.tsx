"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

export default function VerifyPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<string | null>(null);

useEffect(() => {
  if (token) {
    fetch(`http://localhost:8000/verify?token=${token}`)
      .then(async res => {
        const data = await res.json().catch(() => ({}));
        setStatus(data.status || "error");
      })
      .catch(() => setStatus("error"));
  }
}, [token]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-gray-200">
      {status === null && <p>⏳ Verifying your email...</p>}

      {status === "success" && (
        <p className="text-gray-200 font-semibold">
          Your email has been verified! You can now log in. ✅
        </p>
      )}

      {status === "already_verified" && (
        <p className="text-gray-200 font-semibold">
          Your email is already verified. You can log in.
        </p>
      )}

      {status === "expired" && (
        <p className="text-red-600 font-semibold">
          ❌ Verification link expired. Please request a new one.
        </p>
      )}

      {status === "invalid" && (
        <p className="text-red-600 font-semibold">
          ❌ Invalid verification link.
        </p>
      )}

      {status === "error" && (
        <p className="text-red-600 font-semibold">
          ❌ Something went wrong. Try again later.
        </p>
      )}
    </div>
  );
}