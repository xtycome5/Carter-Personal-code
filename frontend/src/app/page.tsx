"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Moon, Sparkles, Video, Image } from "lucide-react";

export default function HomePage() {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
      {/* Background gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#6366f1] opacity-10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#a855f7] opacity-10 rounded-full blur-3xl" />

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 text-center max-w-3xl"
      >
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card mb-8"
        >
          <Moon className="w-4 h-4 text-[#a855f7]" />
          <span className="text-sm text-[#94a3b8]">AI-Powered Dream Visualization</span>
        </motion.div>

        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          <span className="bg-gradient-to-r from-[#6366f1] via-[#a855f7] to-[#ec4899] bg-clip-text text-transparent">
            记录你的梦境
          </span>
          <br />
          <span className="text-white">让 AI 帮你重现</span>
        </h1>

        <p className="text-lg md:text-xl text-[#94a3b8] mb-10 max-w-2xl mx-auto">
          醒来后描述你的梦，AI 将为你生成精美的图片和视频，
          让每一个梦境都能被看见、被保存、被分享。
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/auth"
            className="dream-button text-lg px-8 py-4 inline-flex items-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            免费开始
          </Link>
          <Link
            href="#features"
            className="px-8 py-4 rounded-xl border border-[#2a2a5e] text-[#94a3b8] hover:text-white hover:border-[#6366f1] transition-all inline-flex items-center gap-2"
          >
            了解更多
          </Link>
        </div>
      </motion.div>

      {/* Features Section */}
      <motion.div
        id="features"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="relative z-10 mt-32 w-full max-w-5xl"
      >
        <h2 className="text-3xl font-bold text-center mb-12 text-white">
          两大核心功能
        </h2>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Image Generation */}
          <div className="glass-card p-8 hover:border-[#6366f1]/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#a855f7] flex items-center justify-center mb-6">
              <Image className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">梦境生图</h3>
            <p className="text-[#94a3b8] mb-4">
              将梦境描述转化为精美图片。支持多种艺术风格：水彩梦幻、赛博朋克、古典油画、宫崎骏风等。
            </p>
            <div className="flex flex-wrap gap-2">
              {["超现实", "水彩", "赛博朋克", "宫崎骏", "暗黑哥特"].map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 rounded-full text-xs bg-[#6366f1]/10 text-[#818cf8] border border-[#6366f1]/20"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Video Generation */}
          <div className="glass-card p-8 hover:border-[#a855f7]/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#a855f7] to-[#ec4899] flex items-center justify-center mb-6">
              <Video className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">梦境生视频</h3>
            <p className="text-[#94a3b8] mb-4">
              将梦境转化为 5-15 秒短视频。支持 720P/1080P，多种画面比例，让梦境"动起来"。
            </p>
            <div className="flex flex-wrap gap-2">
              {["梦境回放", "关键片段", "梦境循环", "梦境延续"].map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 rounded-full text-xs bg-[#a855f7]/10 text-[#c084fc] border border-[#a855f7]/20"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Footer */}
      <footer className="relative z-10 mt-24 mb-8 text-center text-[#64748b] text-sm">
        <p>Dream Recorder &copy; 2025 - AI 梦境记录器</p>
      </footer>
    </div>
  );
}
