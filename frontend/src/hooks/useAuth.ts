import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as authApi from "../api/auth";
import { User } from "../types";

const TOKEN_KEY = "docmind_token";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const me = await authApi.getMe();
      setUser(me);
    } catch {
      localStorage.removeItem(TOKEN_KEY);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const doLogin = async (email: string, password: string) => {
    const { access_token } = await authApi.login(email, password);
    localStorage.setItem(TOKEN_KEY, access_token);
    await loadUser();
    navigate("/dashboard");
  };

  const doSignup = async (email: string, password: string, fullName?: string) => {
    const { access_token } = await authApi.signup(email, password, fullName);
    localStorage.setItem(TOKEN_KEY, access_token);
    await loadUser();
    navigate("/dashboard");
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    navigate("/login");
  };

  return { user, loading, doLogin, doSignup, logout, isAuthenticated: !!user };
}
