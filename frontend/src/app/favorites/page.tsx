"use client";

import { Star } from "lucide-react";

export default function FavoritesPage() {
  return (
    <div className="main-content min-h-screen px-8 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Favorites</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Your saved dream visualizations
          </p>
        </div>

        <div className="text-center py-24">
          <div className="w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] flex items-center justify-center mx-auto mb-4">
            <Star className="w-7 h-7 text-[var(--text-muted)]" />
          </div>
          <p className="text-[var(--text-secondary)] mb-2">No favorites yet</p>
          <p className="text-sm text-[var(--text-muted)]">
            Star your best dream visualizations to find them here
          </p>
        </div>
      </div>
    </div>
  );
}
