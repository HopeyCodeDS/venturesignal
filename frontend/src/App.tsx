import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import CompanyCard from "./components/CompanyCard";
import CompanyTable from "./components/CompanyTable";
import Dashboard from "./components/Dashboard";
import Filters from "./components/Filters";
import { fetchCompanies } from "./services/api";
import type { Company, Filters as FiltersType } from "./types";
import "./App.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000 } },
});

function AppContent() {
  const [filters, setFilters] = useState<FiltersType>({
    stage: "",
    industry: "",
    batch: "",
    min_score: "",
    search: "",
  });
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [page, setPage] = useState(1);

  const { data: companies = [], isLoading } = useQuery({
    queryKey: ["companies", filters, page],
    queryFn: () =>
      fetchCompanies({
        ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== "")),
        page,
        limit: 50,
      }),
  });

  return (
    <div className="app">
      <header className="app-header">
        <h1>VentureSignal</h1>
        <p className="subtitle">AI-Powered B2B SaaS Startup Screener</p>
      </header>

      <Dashboard />

      <section className="main-section">
        <Filters filters={filters} onChange={(f) => { setFilters(f); setPage(1); }} />
        <CompanyTable
          companies={companies}
          onSelect={setSelectedCompany}
          isLoading={isLoading}
        />
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <span>Page {page}</span>
          <button disabled={companies.length < 50} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      </section>

      {selectedCompany && (
        <CompanyCard company={selectedCompany} onClose={() => setSelectedCompany(null)} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
