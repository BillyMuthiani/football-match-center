"use client";
import { useEffect, useState } from "react";
import axios from "axios";

interface Match {
  home_team: string;
  away_team: string;
  match_time: string;
  league: string;
}

export default function MatchList() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/matches");
        setMatches(res.data.matches);
      } catch (err) {
        console.error(err);
        setError("Failed to fetch matches");
      } finally {
        setLoading(false);
      }
    };
    fetchMatches();
  }, []);

  if (loading) return <p className="text-center mt-10 text-gray-500">Loading matches...</p>;
  if (error) return <p className="text-center mt-10 text-red-500">{error}</p>;

  return (
    <div className="max-w-3xl mx-auto mt-10">
      <h2 className="text-3xl font-bold text-center mb-6 text-blue-700">
        Upcoming Matches
      </h2>
      <div className="grid gap-4">
        {matches.map((m, idx) => (
          <div key={idx} className="p-4 bg-white shadow rounded-xl flex justify-between items-center">
            <span className="font-semibold text-gray-800">{m.home_team}</span>
            <span className="text-gray-500">vs</span>
            <span className="font-semibold text-gray-800">{m.away_team}</span>
            <span className="text-sm text-gray-600">{m.match_time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
