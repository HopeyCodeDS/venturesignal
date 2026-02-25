export interface Company {
  id: number;
  name: string;
  slug: string;
  website: string | null;
  one_liner: string | null;
  long_description: string | null;
  industry: string | null;
  subindustry: string | null;
  status: string | null;
  stage: string | null;
  team_size: number | null;
  batch: string | null;
  tags: string[];
  regions: string[];
  enriched_text: string | null;
  enriched_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  thesis_fit: number | null;
  market_timing: number | null;
  product_clarity: number | null;
  team_signal: number | null;
  overall_signal: number | null;
  one_line_verdict: string | null;
}

export interface ScoreDetail {
  id: number;
  company_id: number;
  thesis_fit: number;
  market_timing: number;
  product_clarity: number;
  team_signal: number;
  overall_signal: number;
  one_line_verdict: string | null;
  reasoning: string | null;
  model_used: string | null;
  scored_at: string | null;
}

export interface CompanyDetail {
  company: Company;
  score_detail: ScoreDetail | null;
}

export interface Stats {
  total_companies: number;
  scored_companies: number;
  enriched_companies: number;
  avg_overall_signal: number;
  top_industries: { name: string; count: number }[];
  top_companies: { name: string; overall_signal: number; verdict: string }[];
  stage_breakdown: { name: string; count: number }[];
}

export interface Filters {
  stage: string;
  industry: string;
  batch: string;
  min_score: string;
  search: string;
}
