"use client";

import { useState, useCallback } from "react";

interface Props {
  onSearch: (q: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export default function SearchBar({ onSearch, loading, placeholder }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const q = value.trim();
      if (q) onSearch(q);
    },
    [value, onSearch]
  );

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder ?? "Search lectures…"}
        className="input flex-1"
        style={{ fontSize: "1rem", padding: "0.75rem 1rem" }}
        autoComplete="off"
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="btn btn-primary"
        style={{ padding: "0.75rem 1.5rem", fontSize: "0.9375rem" }}
      >
        {loading ? (
          <span className="dot-pulse">
            <span />
            <span />
            <span />
          </span>
        ) : (
          "Search"
        )}
      </button>
    </form>
  );
}
