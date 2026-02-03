import { api, apiFetch, setAuthToken } from "./client";
import { setClientUserId } from "@/lib/user";
import { DEMO_MODE } from "@/config/demo";
import { demoUser } from "@/demo/demoUser";

type TokenResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
};

export async function signup(email: string, password: string) {
  if (DEMO_MODE) {
    setAuthToken("demo");
    setClientUserId(demoUser.id);
    return Promise.resolve({
      access_token: "demo",
      token_type: "bearer",
      user_id: demoUser.id,
      email,
    });
  }
  const data = await api.post<TokenResponse>("/auth/signup", { email, password });
  setAuthToken(data.access_token);
  setClientUserId(data.user_id);
  return data;
}

export async function login(email: string, password: string) {
  if (DEMO_MODE) {
    setAuthToken("demo");
    setClientUserId(demoUser.id);
    return Promise.resolve({
      access_token: "demo",
      token_type: "bearer",
      user_id: demoUser.id,
      email,
    });
  }
  const data = await api.post<TokenResponse>("/auth/login-json", { email, password });
  setAuthToken(data.access_token);
  setClientUserId(data.user_id);
  return data;
}

export async function me() {
  if (DEMO_MODE) {
    return Promise.resolve({ ok: true, user_id: demoUser.id, email: "demo@teski.app" });
  }
  return api.get<{ ok: boolean; user_id: string; email: string }>("/auth/me");
}

export function logout() {
  if (DEMO_MODE) return;
  setAuthToken(null);
  setClientUserId("00000000-0000-0000-0000-000000000000");
}
