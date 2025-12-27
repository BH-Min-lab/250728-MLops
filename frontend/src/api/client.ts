// src/api/client.ts
export const API_BASE_URL =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "http://backend:8000";

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log("[apiFetch] 호출 URL:", url);

  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!res.ok) {
    const errorText = await res.text();
    console.error("[apiFetch] 응답 실패:", res.status, errorText);
    throw new Error(`API 요청 실패: ${res.status} - ${errorText}`);
  }

  return res.json();
}
