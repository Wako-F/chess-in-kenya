"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function PlayerEntryPage() {
  const [username, setUsername] = useState("");
  const router = useRouter();

  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Player route</p>
          <h1>Open Player Profile</h1>
          <p className="lead">
            Jump directly to a player intelligence page by username.
          </p>
        </div>
      </section>
      <section className="panel stagger">
        <div className="search-row">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter username"
            onKeyDown={(e) => {
              if (e.key === "Enter" && username.trim()) {
                router.push(`/player/${username.trim().toLowerCase()}`);
              }
            }}
          />
          <button
            onClick={() => {
              if (username.trim()) router.push(`/player/${username.trim().toLowerCase()}`);
            }}
            disabled={!username.trim()}
          >
            Open Profile
          </button>
        </div>
      </section>
    </main>
  );
}

