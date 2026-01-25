import { api, apiFetch, setAuthToken } from "./client";

type TokenResponse = {
  access_token: string;
  token_type: string;
};

export async function signup(email: string, password: string) {
  const data = await api.post<TokenResponse>("/auth/signup", { email, password });
  setAuthToken(data.access_token);
  return data;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const data = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  setAuthToken(data.access_token);
  return data;
}
