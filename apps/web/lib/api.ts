const API_URL = "http://localhost:8000";

export async function apiFetch(path: string, options: RequestInit = {}) {
console.log("fetching1:", `${API_URL}${path}`);
  const token = localStorage.getItem("access_token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  console.log("fetching2:", `${API_URL}${path}`);
  return res.json();
}