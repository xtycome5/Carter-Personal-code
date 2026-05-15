"use client";

import { motion } from "framer-motion";
import { Compass } from "lucide-react";

export default function ExplorePage() {
  return (
    <div className="main-content min-h-screen px-8 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Explore</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Today's top dream visualizations
          </p>
        </div>

        {/* Placeholder - will be populated by a public API */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-24"
        >
          <div className="w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] flex items-center justify-center mx-auto mb-4">
            <Compass className="w-7 h-7 text-[var(--text-muted)]" />
          </div>
          <p className="text-[var(--text-secondary)] mb-2">Daily Top 20 coming soon</p>
          <p className="text-sm text-[var(--text-muted)]">
            The most beautiful dream visualizations of each day will appear here
          </p>
        </motion.div>
      </div>
    </div>
  );
}
