import { useQuery } from "@tanstack/react-query";
import { fetchStats, triggerIngest, triggerEnrich, triggerScore, triggerRescore } from "../services/api";
import { useState } from "react";

export default function Dashboard() {
  const { data: stats, isLoading, refetch } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });
  const [actionStatus, setActionStatus] = useState("");

  const formatResult = (label: string, result: unknown): string => {
    const r = result as Record<string, unknown>;
    if (r.companies_scored != null) return `${label} complete — ${r.companies_scored} companies scored`;
    if (r.companies_rescored != null) return `${label} complete — ${r.companies_rescored} companies rescored`;
    if (r.companies_ingested != null) return `${label} complete — ${r.companies_ingested} companies ingested`;
    if (r.companies_enriched != null) return `${label} complete — ${r.companies_enriched} companies enriched`;
    if (r.status === "completed" || r.status === "success") return `${label} complete`;
    return `${label} complete`;
  };

  const handleAction = async (action: () => Promise<unknown>, label: string) => {
    setActionStatus(`Running ${label}...`);
    try {
      const result = await action();
      setActionStatus(formatResult(label, result));
      refetch();
    } catch {
      setActionStatus(`${label} failed`);
    }
  };

  if (isLoading) return <div className="loading">Loading stats...</div>;
  if (!stats) return <div>No stats available</div>;

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total_companies}</div>
          <div className="stat-label">Total Companies</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.enriched_companies}</div>
          <div className="stat-label">Enriched</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.scored_companies}</div>
          <div className="stat-label">Scored</div>
        </div>
        <div className="stat-card accent">
          <div className="stat-value">{stats.avg_overall_signal}</div>
          <div className="stat-label">Avg Signal</div>
        </div>
      </div>

      <div className="actions">
        <button onClick={() => handleAction(triggerIngest, "Ingest")}>
          Ingest Companies
        </button>
        <button onClick={() => handleAction(triggerEnrich, "Enrich")}>
          Enrich Websites
        </button>
        <button onClick={() => handleAction(() => triggerScore(20), "Score")}>
          Score Batch (20)
        </button>
        <button onClick={() => handleAction(() => triggerRescore(20), "Rescore All")} style={{ background: "#dc2626" }}>
          Rescore All
        </button>
        {actionStatus && <span className="action-status">{actionStatus}</span>}
      </div>

      {stats.top_companies.length > 0 && (
        <div className="top-companies">
          <h3>Top Scored Companies</h3>
          <div className="top-list">
            {stats.top_companies.map((c, i) => (
              <div key={i} className="top-item">
                <span className="top-rank">#{i + 1}</span>
                <span className="top-name">{c.name}</span>
                <span className="top-score">{c.overall_signal}/10</span>
                <span className="top-verdict">{c.verdict}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
