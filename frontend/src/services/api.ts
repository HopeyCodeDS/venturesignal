import axios from "axios";
import type { Company, CompanyDetail, Stats } from "../types";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
});

export async function fetchCompanies(params: Record<string, string | number>): Promise<Company[]> {
  const cleaned = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== "" && v !== undefined)
  );
  const { data } = await api.get<Company[]>("/companies", { params: cleaned });
  return data;
}

export async function fetchCompany(id: number): Promise<CompanyDetail> {
  const { data } = await api.get<CompanyDetail>(`/companies/${id}`);
  return data;
}

export async function fetchStats(): Promise<Stats> {
  const { data } = await api.get<Stats>("/stats");
  return data;
}

export async function triggerIngest(): Promise<{ status: string; companies_upserted: number }> {
  const { data } = await api.post("/ingest");
  return data;
}

export async function triggerEnrich(): Promise<{ status: string; companies_enriched: number }> {
  const { data } = await api.post("/enrich");
  return data;
}

export async function triggerScore(batchSize = 20): Promise<{ status: string; companies_scored: number }> {
  const { data } = await api.post("/score", null, { params: { batch_size: batchSize } });
  return data;
}

export async function triggerRescore(batchSize = 20): Promise<{ status: string; companies_rescored: number }> {
  const { data } = await api.post("/rescore", null, { params: { batch_size: batchSize } });
  return data;
}
