"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";

interface AuditRow {
  id: string;
  timestamp: string;
  agent_id: string;
  decision_type: string;
  confidence_score: number | null;
  entity_id: string | null;
  input_hash?: string;
  output_hash?: string;
  regulatory_citations?: unknown;
  human_override?: string;
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState("");

  function fetchLog() {
    api.lifecycle.auditLog({ limit: 100, entity_id: entityFilter || undefined })
      .then((r) => setEntries(Array.isArray(r) ? r : []))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchLog();
    const t = setInterval(fetchLog, 10000);
    return () => clearInterval(t);
  }, [entityFilter]);

  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-2xl font-semibold">Audit log (live)</h2>
      <p className="text-slate-400">
        EU AI Act Article 12 – record-keeping. Entries from PostgreSQL audit_log. Polls every 10s. Retention: 10 years.
      </p>
      <div className="flex gap-2 items-center">
        <label className="text-sm text-slate-400">Filter by entity_id</label>
        <input
          type="text"
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          placeholder="optional"
          className="rounded bg-slate-800 border border-slate-600 px-2 py-1 text-sm w-48"
        />
      </div>
      {loading && entries.length === 0 ? (
        <p className="text-slate-500">Loading…</p>
      ) : entries.length === 0 ? (
        <div className="rounded-lg border border-slate-700 p-6 text-center text-slate-500">
          No audit entries yet. Agent decisions will appear here.
        </div>
      ) : (
        <div className="rounded-lg border border-slate-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-800 text-left text-slate-300">
                <th className="px-4 py-2">Time</th>
                <th className="px-4 py-2">Agent</th>
                <th className="px-4 py-2">Decision</th>
                <th className="px-4 py-2">Confidence</th>
                <th className="px-4 py-2">Entity ID</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-t border-slate-700 hover:bg-slate-800/50">
                  <td className="px-4 py-2 text-slate-400">{e.timestamp}</td>
                  <td className="px-4 py-2">{e.agent_id}</td>
                  <td className="px-4 py-2">{e.decision_type}</td>
                  <td className="px-4 py-2">{e.confidence_score != null ? String(e.confidence_score) : "—"}</td>
                  <td className="px-4 py-2 text-slate-400">{e.entity_id ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
