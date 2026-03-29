import axios from "axios";

function getSessionId() {
  let id = localStorage.getItem("jobradar_session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("jobradar_session_id", id);
  }
  return id;
}

const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

const api = axios.create({
  baseURL: BASE,
  headers: { "X-Session-ID": getSessionId() },
});

// ── Jobs ──────────────────────────────────────────────────────────────────────
export const getJobs = (tab = "feed") => api.get("/jobs", { params: { tab } });
export const updateJobStatus = (jobId, status) =>
  api.patch(`/jobs/${jobId}/status`, { status });

// ── Criteria ──────────────────────────────────────────────────────────────────
export const getCriteria = () => api.get("/settings/criteria");
export const saveCriteria = (data) => api.put("/settings/criteria", data);

// ── Companies ─────────────────────────────────────────────────────────────────
export const getCompanyDirectory = () => api.get("/settings/company-directory");
export const getCompanies = () => api.get("/settings/companies");
export const addCompany = (source, slug) =>
  api.post("/settings/companies", { source, slug });
export const deleteCompany = (id) => api.delete(`/settings/companies/${id}`);

// ── Sectors ───────────────────────────────────────────────────────────────────
export const getSectors = () => api.get("/sectors");
export const addSector = (name) => api.post("/sectors/add", null, { params: { sector_name: name } });
export const removeSector = (name) => api.delete("/sectors", { params: { sector_name: name } });

// ── Scraper ───────────────────────────────────────────────────────────────────
export const triggerScrape = () => api.post("/scraper/run");
export const getScoringStatus = () => api.get("/scraper/status");

export default api;
