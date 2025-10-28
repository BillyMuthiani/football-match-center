"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [league, setLeague] = useState("PL");

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/matches?league=${league}`)
      .then(res => res.json())
      .then(data => {
        setMatches(data.matches || []);
        setLoading(false);
      });
  }, [league]);

  return (
    <main className="min-h-screen bg-gray-950 text-white px-6 py-10">
      <h1 className="text-3xl font-bold mb-6">⚽ Football Match Center</h1>

      {/* League selector */}
      <div className="flex gap-3 mb-6">
        {["Premier League", "Serie A", "La Liga", "Bundesliga", "Ligue 1"].map(l => (
          <button
            key={l}
            className={`px-4 py-2 rounded-lg ${
              league === l ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"
            }`}
            onClick={() => {
              setLoading(true);
              setLeague(l);
            }}
          >
            {l}
          </button>
        ))}
      </div>

      <h2 className="text-xl font-semibold mb-4">
        Upcoming Matches ({league})
      </h2>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {matches.length > 0 ? (
            matches.map((m, i) => (
              <div
                key={i}
                className="bg-gray-800 rounded-xl p-4 flex flex-col items-center shadow-lg"
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex flex-col items-center">
                    
                    <img
                      src={m.home_logo}
                      alt={m.home_team}
                      className="w-12 h-12 object-contain mb-1"
                    />
                    <span className="text-sm">{m.home_team}</span>
                  </div>

                  <span className="text-lg font-semibold">vs</span>

                  <div className="flex flex-col items-center">
                    <img
                      src={m.away_logo}
                      alt={m.away_team}
                      className="w-12 h-12 object-contain mb-1"
                    />
                    <span className="text-sm">{m.away_team}</span>
                  </div>
                </div>
                <p className="text-sm text-gray-400 mt-2">
                  {new Date(m.date).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">{m.venue}</p>
              </div>
            ))
          ) : (
            <p>No matches found for the next few days.</p>
          )}
        </div>
      )}
    </main>
  );
}
