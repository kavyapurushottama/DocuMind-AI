import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function EyeIcon({ open }: { open: boolean }) {
  return open ? (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ) : (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
    </svg>
  );
}

function HeroBranding() {
  return (
    <div className="hidden lg:flex lg:w-1/2 relative flex-col items-center justify-center p-12 overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute -top-20 -left-20 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
      <div className="absolute -bottom-10 -right-10 h-56 w-56 rounded-full bg-violet/20 blur-3xl" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-white/5 blur-2xl" />

      <div className="relative z-10 text-center text-white animate-fade-up">
        {/* Logo icon */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-white/15 shadow-float backdrop-blur-sm border border-white/20">
          <svg className="h-10 w-10" viewBox="0 0 40 40" fill="none">
            <path d="M20 4C11.163 4 4 11.163 4 20s7.163 16 16 16 16-7.163 16-16S28.837 4 20 4z" fill="white" fillOpacity="0.2"/>
            <path d="M14 15h12M14 20h8M14 25h10" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
            <circle cx="28" cy="28" r="6" fill="white" fillOpacity="0.9"/>
            <path d="M26 28h4M28 26v4" stroke="#5B6FFF" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>

        <h1 className="font-display text-4xl font-bold tracking-tight">DocuMind AI</h1>
        <p className="mt-3 text-lg text-white/80 max-w-xs mx-auto leading-relaxed">
          Your documents, answered instantly — with cited sources.
        </p>

        <div className="mt-10 space-y-4 text-left max-w-xs mx-auto">
          {[
            { icon: "📄", text: "Upload PDF, DOCX, TXT, Markdown" },
            { icon: "💬", text: "Ask questions in plain English" },
            { icon: "🎯", text: "Get answers with page citations" },
          ].map((f) => (
            <div key={f.text} className="flex items-center gap-3 rounded-2xl bg-white/10 px-4 py-3 backdrop-blur-sm border border-white/10">
              <span className="text-xl">{f.icon}</span>
              <span className="text-sm text-white/90 font-medium">{f.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  const { doLogin } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await doLogin(email, password);
    } catch (err: any) {
      if (!err?.response) {
        setError("Unable to connect to backend server. Please verify your API deployment and VITE_API_URL.");
      } else {
        setError(err?.response?.data?.detail || "Incorrect email or password");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen" style={{ background: 'linear-gradient(135deg, #0c1445 0%, #1e3a8a 40%, #2563eb 100%)' }}>
      <HeroBranding />

      {/* Right: form panel */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 lg:px-16 bg-white rounded-3xl shadow-xl m-4 lg:m-0 lg:rounded-none lg:rounded-l-3xl">
        {/* Mobile brand header */}
        <div className="mb-8 flex items-center gap-2 lg:hidden">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-hero-gradient shadow">
            <span className="text-lg">🧠</span>
          </div>
          <span className="font-display text-xl font-bold text-ink">DocuMind AI</span>
        </div>

        <div className="w-full max-w-sm animate-fade-up">
          <h2 className="font-display text-2xl font-bold text-ink">Welcome back</h2>
          <p className="mt-1 text-sm text-t3">Log in to your knowledge base</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5" id="login-form">
            {/* Email */}
            <div>
              <label htmlFor="login-email" className="mb-1.5 block text-xs font-semibold text-t2 uppercase tracking-wide">
                Email address
              </label>
              <input
                id="login-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-xl border border-t4 bg-white px-4 py-2.5 text-sm text-ink placeholder-t4 transition hover:border-accent/40 focus:border-accent focus:ring-0"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-xs font-semibold text-t2 uppercase tracking-wide">
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-t4 bg-white px-4 py-2.5 pr-10 text-sm text-ink placeholder-t4 transition hover:border-accent/40 focus:border-accent focus:ring-0"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-t3 hover:text-accent transition"
                  aria-label="Toggle password visibility"
                >
                  <EyeIcon open={showPassword} />
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 rounded-xl border border-danger/20 bg-red-50 px-4 py-3 text-sm text-danger">
                <svg className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" /></svg>
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="relative w-full overflow-hidden rounded-xl bg-accent py-2.5 text-sm font-semibold text-white shadow-md transition hover:bg-accentDark hover:shadow-glow-lg disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
                  </svg>
                  Logging in...
                </span>
              ) : (
                "Log in"
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-t3">
            No account?{" "}
            <Link to="/signup" className="font-semibold text-accent hover:text-accentDark">
              Sign up free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
