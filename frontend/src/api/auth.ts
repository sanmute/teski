import { api, apiFetch, setAuthToken } from "./client";
import { setClientUserId } from "@/lib/user";

type TokenResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
};

export async function signup(email: string, password: string) {
  const data = await api.post<TokenResponse>("/auth/signup", { email, password });
  setAuthToken(data.access_token);
  setClientUserId(data.user_id);
  return data;
}

export async function login(email: string, password: string) {
  const data = await api.post<TokenResponse>("/auth/login-json", { email, password });
  setAuthToken(data.access_token);
  setClientUserId(data.user_id);
  return data;
}

export async function me() {
  return api.get<{ ok: boolean; user_id: string; email: string }>("/auth/me");
}

export function logout() {
  setAuthToken(null);
  setClientUserId("00000000-0000-0000-0000-000000000000");
}
  });
  setAuthToken(data.access_token);
  return data;
}
