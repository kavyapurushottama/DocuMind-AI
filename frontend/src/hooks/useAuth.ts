import React, { createContext, useContext, useCallback, useEffect, useState, ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import * as authApi from "../api/auth";
import { User } from "../types";

const TOKEN_KEY = "docmind_token";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  doLogin: (email: string, password: string) => Promise<void>;
  doSignup: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await authApi.getMe();
      setUser(me);
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
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

  return React.createElement(
    AuthContext.Provider,
    { value: { user, loading, doLogin, doSignup, logout, isAuthenticated: !!user } },
    children
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
