import type { Filters as FiltersType } from "../types";

interface Props {
  filters: FiltersType;
  onChange: (filters: FiltersType) => void;
}

const STAGES = ["", "Seed", "Series A", "Series B", "Series C", "Growth", "IPO"];
const SCORES = ["", "5", "6", "7", "8", "9"];

export default function Filters({ filters, onChange }: Props) {
  const update = (key: keyof FiltersType, value: string) => {
    onChange({ ...filters, [key]: value });
  };

  return (
    <div className="filters">
      <input
        type="text"
        placeholder="Search companies..."
        value={filters.search}
        onChange={(e) => update("search", e.target.value)}
        className="search-input"
      />
      <select value={filters.stage} onChange={(e) => update("stage", e.target.value)}>
        <option value="">All Stages</option>
        {STAGES.filter(Boolean).map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <input
        type="text"
        placeholder="Industry..."
        value={filters.industry}
        onChange={(e) => update("industry", e.target.value)}
      />
      <input
        type="text"
        placeholder="Batch (e.g. S21)..."
        value={filters.batch}
        onChange={(e) => update("batch", e.target.value)}
      />
      <select value={filters.min_score} onChange={(e) => update("min_score", e.target.value)}>
        <option value="">Min Score</option>
        {SCORES.filter(Boolean).map((s) => (
          <option key={s} value={s}>{s}+</option>
        ))}
      </select>
    </div>
  );
}
