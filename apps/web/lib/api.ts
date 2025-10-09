export async function apiFetch(path: string, options: RequestInit = {}) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const token = localStorage.getItem("access_token");

  let res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  // If token expired → try refresh
  if (res.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      res = await fetch(`${baseUrl}${path}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${refreshed}`,
          ...options.headers,
        },
      });
    }
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw errorData;
  }

  return res.json();
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return null;

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const res = await fetch(`${baseUrl}/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) return null;

  const data = await res.json().catch(() => ({}));
  localStorage.setItem("access_token", data.access_token);
  return data.access_token;
}
