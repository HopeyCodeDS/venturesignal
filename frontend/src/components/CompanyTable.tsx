import type { Company } from "../types";

interface Props {
  companies: Company[];
  onSelect: (company: Company) => void;
  isLoading: boolean;
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="score-badge none">--</span>;
  const color = score >= 8 ? "high" : score >= 6 ? "mid" : "low";
  return <span className={`score-badge ${color}`}>{score}</span>;
}

export default function CompanyTable({ companies, onSelect, isLoading }: Props) {
  if (isLoading) return <div className="loading">Loading companies...</div>;
  if (companies.length === 0) return <div className="empty">No companies found. Try ingesting data first.</div>;

  return (
    <div className="table-wrapper">
      <table className="company-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>One-Liner</th>
            <th>Industry</th>
            <th>Stage</th>
            <th>Batch</th>
            <th>Team</th>
            <th>Signal</th>
            <th>Fit</th>
            <th>Verdict</th>
          </tr>
        </thead>
        <tbody>
          {companies.map((c) => (
            <tr key={c.id} onClick={() => onSelect(c)} className="clickable">
              <td className="name-cell">
                <strong>{c.name}</strong>
              </td>
              <td className="oneliner-cell">{c.one_liner || "—"}</td>
              <td>{c.industry || "—"}</td>
              <td>{c.stage || "—"}</td>
              <td>{c.batch || "—"}</td>
              <td>{c.team_size || "—"}</td>
              <td><ScoreBadge score={c.overall_signal} /></td>
              <td><ScoreBadge score={c.thesis_fit} /></td>
              <td className="verdict-cell">{c.one_line_verdict || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
