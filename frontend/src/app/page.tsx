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
            Record Your Dreams
          </span>
          <br />
          <span className="text-white">Let AI Bring Them to Life</span>
        </h1>

        <p className="text-lg md:text-xl text-[#94a3b8] mb-10 max-w-2xl mx-auto">
          Describe your dreams after waking up. AI will generate stunning images
          and videos, so every dream can be seen, saved, and shared.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/auth"
            className="dream-button text-lg px-8 py-4 inline-flex items-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            Get Started Free
          </Link>
          <Link
            href="#features"
            className="px-8 py-4 rounded-xl border border-[#2a2a5e] text-[#94a3b8] hover:text-white hover:border-[#6366f1] transition-all inline-flex items-center gap-2"
          >
            Learn More
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
          Two Core Features
        </h2>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Image Generation */}
          <div className="glass-card p-8 hover:border-[#6366f1]/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#a855f7] flex items-center justify-center mb-6">
              <Image className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Dream to Image</h3>
            <p className="text-[#94a3b8] mb-4">
              Transform dream descriptions into beautiful images. Supports multiple art styles: watercolor, cyberpunk, classical oil painting, Ghibli, and more.
            </p>
            <div className="flex flex-wrap gap-2">
              {["Surreal", "Watercolor", "Cyberpunk", "Ghibli", "Gothic"].map((tag) => (
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
            <h3 className="text-xl font-bold text-white mb-3">Dream to Video</h3>
            <p className="text-[#94a3b8] mb-4">
              Turn dreams into 5-second cinematic clips. Supports 720P/1080P with multiple aspect ratios. Bring your dreams to motion.
            </p>
            <div className="flex flex-wrap gap-2">
              {["Replay", "Key Scene", "Loop", "Continuation"].map((tag) => (
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
        <p>Dream Recorder &copy; 2025 - AI Dream Visualizer</p>
      </footer>
    </div>
  );
}
