import { useQuery } from "@tanstack/react-query";
import { fetchCompany } from "../services/api";
import type { Company } from "../types";

interface Props {
  company: Company;
  onClose: () => void;
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = (score / 10) * 100;
  const color = score >= 8 ? "#22c55e" : score >= 6 ? "#eab308" : "#ef4444";
  return (
    <div className="score-bar">
      <div className="score-bar-label">
        <span>{label}</span>
        <span>{score}/10</span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

export default function CompanyCard({ company, onClose }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["company", company.id],
    queryFn: () => fetchCompany(company.id),
  });

  const detail = data?.score_detail;
  let reasoning: Record<string, string> = {};
  if (detail?.reasoning) {
    try {
      reasoning = JSON.parse(detail.reasoning);
    } catch {
      /* ignore parse errors */
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&times;</button>

        <div className="modal-header">
          <h2>{company.name}</h2>
          {company.website && (
            <a href={company.website} target="_blank" rel="noopener noreferrer" className="website-link">
              {company.website}
            </a>
          )}
        </div>

        <p className="company-oneliner">{company.one_liner}</p>

        <div className="company-meta">
          {company.industry && <span className="tag">{company.industry}</span>}
          {company.stage && <span className="tag">{company.stage}</span>}
          {company.batch && <span className="tag">{company.batch}</span>}
          {company.team_size && <span className="tag">{company.team_size} people</span>}
          {company.status && <span className="tag">{company.status}</span>}
        </div>

        {company.long_description && (
          <div className="company-description">
            <h4>Description</h4>
            <p>{company.long_description}</p>
          </div>
        )}

        {isLoading ? (
          <div className="loading">Loading scores...</div>
        ) : detail ? (
          <div className="scores-section">
            <h4>Investment Scores</h4>
            <ScoreBar label="Overall Signal" score={detail.overall_signal} />
            <ScoreBar label="Thesis Fit" score={detail.thesis_fit} />
            <ScoreBar label="Market Timing" score={detail.market_timing} />
            <ScoreBar label="Product Clarity" score={detail.product_clarity} />
            <ScoreBar label="Team Signal" score={detail.team_signal} />

            {detail.one_line_verdict && (
              <div className="verdict-box">
                <strong>Verdict:</strong> {detail.one_line_verdict}
              </div>
            )}

            {Object.keys(reasoning).length > 0 && (
              <div className="reasoning-section">
                <h4>Detailed Reasoning</h4>
                {Object.entries(reasoning).map(([key, value]) => (
                  <div key={key} className="reasoning-item">
                    <strong>{key.replace(/_/g, " ")}:</strong> {value}
                  </div>
                ))}
              </div>
            )}

            {detail.model_used && (
              <div className="model-info">
                Scored by {detail.model_used} on {detail.scored_at?.split("T")[0]}
              </div>
            )}
          </div>
        ) : (
          <div className="no-scores">Not scored yet</div>
        )}
      </div>
    </div>
  );
}
