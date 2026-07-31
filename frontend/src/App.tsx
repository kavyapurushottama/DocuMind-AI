import { useState } from "react";
import { Navigate, Route, Routes, Link, useLocation } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";

const NAV_LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/chat",      label: "Chat" },
];

function BrainIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 40 40" fill="none">
      <rect width="40" height="40" rx="10" fill="url(#logo-grad)" />
      <path d="M12 15h16M12 20h10M12 25h13" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="30" cy="30" r="5" fill="white" fillOpacity="0.95" />
      <path d="M28.5 30h3M30 28.5v3" stroke="#5B6FFF" strokeWidth="1.8" strokeLinecap="round" />
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop stopColor="#5B6FFF" />
          <stop offset="1" stopColor="#8B5CF6" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function UserAvatar({ name, email }: { name?: string | null; email: string }) {
  const initials = name
    ? name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : email[0].toUpperCase();

  const [open, setOpen] = useState(false);
  const { logout } = useAuth();

  return (
    <div className="relative">
      <button
        id="user-avatar-btn"
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-xs font-bold text-white shadow transition hover:ring-2 hover:ring-accent/40"
      >
        {initials}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-10 z-40 w-52 rounded-2xl border border-t4/60 bg-white p-1 shadow-float animate-fade-up">
            <div className="border-b border-t4/40 px-3 py-2.5">
              <p className="text-xs font-semibold text-ink truncate">{name || "User"}</p>
              <p className="text-[11px] text-t3 truncate">{email}</p>
            </div>
            <button
              onClick={() => { setOpen(false); logout(); }}
              className="mt-1 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-danger hover:bg-red-50 transition"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Log out
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function NavBar() {
  const { user } = useAuth();
  const location = useLocation();

  return (
    <nav className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-black/5 glass px-5">
      {/* Logo */}
      <Link to="/dashboard" className="flex items-center gap-2" id="nav-logo">
        <BrainIcon />
        <span className="font-display text-base font-bold text-ink">DocuMind AI</span>
      </Link>

      {/* Links */}
      <div className="flex items-center gap-1">
        {NAV_LINKS.map(({ to, label }) => {
          const active = location.pathname === to;
          return (
            <Link
              key={to}
              to={to}
              id={`nav-${label.toLowerCase()}`}
              className={`relative rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                active
                  ? "text-accent bg-accentSoft"
                  : "text-t2 hover:text-ink hover:bg-muted"
              }`}
            >
              {label}
              {active && (
                <span className="absolute inset-x-3 -bottom-[11px] h-[2px] rounded-full bg-accent" />
              )}
            </Link>
          );
        })}
      </div>

      {/* User avatar */}
      {user && <UserAvatar name={user.full_name} email={user.email} />}
    </nav>
  );
}

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center gap-2">
        <div className="h-2 w-2 rounded-full bg-accent dot-1" />
        <div className="h-2 w-2 rounded-full bg-accent dot-2" />
        <div className="h-2 w-2 rounded-full bg-accent dot-3" />
      </div>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen bg-paper">
      <NavBar />
      {children}
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login"  element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/dashboard" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
      <Route path="/upload"    element={<Navigate to="/dashboard" replace />} />
      <Route path="/chat"      element={<ProtectedLayout><ChatPage /></ProtectedLayout>} />
      <Route path="*"          element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
