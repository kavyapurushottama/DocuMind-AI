import { apiClient } from "./client";
import { User } from "../types";

export async function signup(email: string, password: string, fullName?: string) {
  const { data } = await apiClient.post("/api/auth/signup", {
    email,
    password,
    full_name: fullName || null,
  });
  return data as { access_token: string; token_type: string };
}

export async function login(email: string, password: string) {
  // backend uses OAuth2PasswordRequestForm -> expects form-encoded username/password
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const { data } = await apiClient.post("/api/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data as { access_token: string; token_type: string };
}

export async function getMe() {
  const { data } = await apiClient.get("/api/auth/me");
  return data as User;
}
