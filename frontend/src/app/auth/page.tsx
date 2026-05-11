"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Moon, Mail, Lock, User, Github } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { authAPI } from "@/lib/api";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
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
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "操作失败，请重试");
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
      setError(`${provider} 登录暂未配置`);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      {/* Background */}
      <div className="absolute top-1/3 left-1/3 w-80 h-80 bg-[#6366f1] opacity-5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/3 right-1/3 w-80 h-80 bg-[#a855f7] opacity-5 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <Moon className="w-10 h-10 text-[#a855f7] mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white">
            {isLogin ? "欢迎回来" : "开始记录梦境"}
          </h1>
          <p className="text-[#94a3b8] mt-2">
            {isLogin ? "登录你的梦境世界" : "创建账户，探索你的潜意识"}
          </p>
        </div>

        {/* Form Card */}
        <div className="glass-card p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
                <input
                  type="text"
                  placeholder="昵称（可选）"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  className="dream-input pl-11"
                />
              </div>
            )}

            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
              <input
                type="email"
                placeholder="邮箱地址"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="dream-input pl-11"
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
              <input
                type="password"
                placeholder="密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="dream-input pl-11"
              />
            </div>

            {error && (
              <p className="text-red-400 text-sm text-center">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="dream-button w-full disabled:opacity-50"
            >
              {loading ? "处理中..." : isLogin ? "登录" : "注册"}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-4 my-6">
            <div className="flex-1 h-px bg-[#2a2a5e]" />
            <span className="text-xs text-[#64748b]">或使用</span>
            <div className="flex-1 h-px bg-[#2a2a5e]" />
          </div>

          {/* OAuth Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => handleOAuth("google")}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border border-[#2a2a5e] text-[#94a3b8] hover:border-[#6366f1] hover:text-white transition-all"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Google
            </button>
            <button
              onClick={() => handleOAuth("github")}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border border-[#2a2a5e] text-[#94a3b8] hover:border-[#6366f1] hover:text-white transition-all"
            >
              <Github className="w-4 h-4" />
              GitHub
            </button>
          </div>

          {/* Toggle */}
          <p className="text-center text-[#94a3b8] text-sm mt-6">
            {isLogin ? "还没有账户？" : "已有账户？"}
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError("");
              }}
              className="text-[#818cf8] hover:text-[#a855f7] ml-1 font-medium"
            >
              {isLogin ? "去注册" : "去登录"}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
