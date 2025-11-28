import { api, setAuthToken } from "./client";

type TokenResponse = {
  access_token: string;
  token_type: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function signup(email: string, password: string) {
  const data = await api.post<TokenResponse>("/auth/signup", { email, password });
  setAuthToken(data.access_token);
  return data;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const data = (await res.json()) as TokenResponse;
  setAuthToken(data.access_token);
  return data;
}
