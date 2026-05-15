"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Mail, Lock, User, Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { authAPI } from "@/lib/api";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let result: any;
      if (isLogin) {
        result = await authAPI.login({ email, password });
      } else {
        result = await authAPI.register({ email, password, nickname });
      }
      setAuth(result.user, result.access_token);
      router.push("/create");
    } catch (err: any) {
      setError(err.message || "Operation failed, please try again");
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: "google" | "github") => {
    try {
      const getUrl =
        provider === "google" ? authAPI.getGoogleOAuthUrl : authAPI.getGitHubOAuthUrl;
      const { url } = await getUrl();
      window.location.href = url;
    } catch (err: any) {
      setError(`${provider} login is not available yet`);
    }
  };

  return (
    <div className="min-h-screen flex auth-layout">
      {/* Left - Artistic Image */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        {/* Dream-like gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#1a0533] via-[#0c1445] to-[#0a0a14]" />
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-[#7c5cfc] rounded-full blur-[100px]" />
          <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-[#c084fc] rounded-full blur-[120px]" />
          <div className="absolute top-2/3 left-1/2 w-64 h-64 bg-[#ec4899] rounded-full blur-[80px]" />
        </div>
        {/* Overlay content */}
        <div className="relative z-10 flex flex-col items-center justify-center w-full p-12">
          <div className="text-center max-w-md">
            <h2 className="text-4xl font-bold text-white mb-4 leading-tight">
              Where Dreams<br />Become Art
            </h2>
            <p className="text-[#a5b4c8] text-lg leading-relaxed">
              Record your dreams and watch AI transform them into 
              surreal paintings and cinematic videos.
            </p>
          </div>
        </div>
      </div>

      {/* Right - Auth Form */}
      <div className="flex-1 flex items-center justify-center p-8 lg:p-16 bg-[var(--bg-primary)]">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          {/* Header */}
          <div className="mb-10">
            <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
              {isLogin ? "Welcome to Dream Recorder" : "Create your account"}
            </h1>
            <p className="text-[var(--text-secondary)]">
              {isLogin
                ? "Sign in to continue your dream journal"
                : "Start recording and visualizing your dreams"}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <input
                  type="text"
                  placeholder="Nickname (optional)"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  className="input-field"
                />
              </div>
            )}

            <div>
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input-field"
              />
            </div>

            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="input-field pr-11"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {error && (
              <p className="text-red-400 text-sm">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full !py-3 !text-[15px]"
            >
              {loading ? "Processing..." : isLogin ? "Log in" : "Sign up"}
            </button>
          </form>

          {/* Toggle + Forgot */}
          <div className="flex items-center justify-between mt-4">
            <p className="text-sm text-[var(--text-secondary)]">
              {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
              <button
                onClick={() => { setIsLogin(!isLogin); setError(""); }}
                className="text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
              >
                {isLogin ? "Sign up" : "Sign in"}
              </button>
            </p>
            {isLogin && (
              <button className="text-sm text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors">
                Forgot Password
              </button>
            )}
          </div>

          {/* Divider */}
          <div className="flex items-center gap-4 my-8">
            <div className="flex-1 h-px bg-[var(--border-subtle)]" />
            <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">or</span>
            <div className="flex-1 h-px bg-[var(--border-subtle)]" />
          </div>

          {/* OAuth Buttons */}
          <div className="space-y-3">
            <button
              onClick={() => handleOAuth("google")}
              className="w-full flex items-center justify-center gap-3 py-3 rounded-xl border border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--border-hover)] hover:bg-[rgba(255,255,255,0.02)] transition-all font-medium"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Log in with Google
            </button>
            <button
              onClick={() => handleOAuth("github")}
              className="w-full flex items-center justify-center gap-3 py-3 rounded-xl border border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--border-hover)] hover:bg-[rgba(255,255,255,0.02)] transition-all font-medium"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Log in with GitHub
            </button>
          </div>

          {/* Footer */}
          <p className="text-center text-xs text-[var(--text-muted)] mt-8">
            By logging in, you accept our{" "}
            <a href="#" className="underline hover:text-[var(--text-secondary)]">Terms of Service</a>
            {" "}and{" "}
            <a href="#" className="underline hover:text-[var(--text-secondary)]">Privacy Policy</a>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
