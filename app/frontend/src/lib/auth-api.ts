export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar_url: string | null;
}

async function refreshToken(): Promise<boolean> {
  const response = await fetch("/api/auth/refresh", { method: "POST" });
  return response.ok;
}

export async function fetchWithRefresh(url: string, options?: RequestInit): Promise<Response> {
  let response = await fetch(url, options);

  if (response.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      response = await fetch(url, options);
    } else {
      window.location.href = "/login";
    }
  }

  return response;
}

export async function fetchCurrentUser(): Promise<User | null> {
  const response = await fetch("/api/auth/me");
  if (!response.ok) return null;
  return response.json();
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" });
}
