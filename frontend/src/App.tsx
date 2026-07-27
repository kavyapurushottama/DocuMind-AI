import { Navigate, Route, Routes, Link, useLocation } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";

function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const linkClass = (path: string) =>
    `text-sm font-medium transition ${
      location.pathname === path ? "text-accent" : "text-ink/60 hover:text-ink"
    }`;

  return (
    <nav className="flex h-16 items-center justify-between border-b border-black/5 bg-white px-6">
      <Link to="/dashboard" className="font-display text-lg font-bold text-ink">
        DocuMind AI
      </Link>
      <div className="flex items-center gap-6">
        <Link to="/dashboard" className={linkClass("/dashboard")}>Dashboard</Link>
        <Link to="/upload" className={linkClass("/upload")}>Upload</Link>
        <Link to="/chat" className={linkClass("/chat")}>Chat</Link>
        {user && (
          <button onClick={logout} className="text-sm text-ink/40 hover:text-red-500 transition">
            Log out
          </button>
        )}
      </div>
    </nav>
  );
}

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-ink/40">Loading...</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
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
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/dashboard" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
      <Route path="/upload" element={<ProtectedLayout><UploadPage /></ProtectedLayout>} />
      <Route path="/chat" element={<ProtectedLayout><ChatPage /></ProtectedLayout>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
