import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import CompanySlugs from "../components/CompanySlugs";
import SectorPicker from "../components/SectorPicker";
import SettingsForm from "../components/SettingsForm";
import { triggerScrape, getScoringStatus, getCompanies, getCriteria } from "../api/client";

export default function Settings() {
  const [scrapeResult, setScrapeResult] = useState(null);
  const [scraping, setScraping] = useState(false);
  const [scoring, setScoring] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [hasTitles, setHasTitles] = useState(false);
  const pollRef = useRef(null);

  async function refreshCompanies() {
    const { data } = await getCompanies();
    setCompanies(data);
  }

  async function refreshCriteria() {
    const { data } = await getCriteria();
    setHasTitles(data.titles && data.titles.length > 0);
  }

  useEffect(() => {
    refreshCompanies();
    refreshCriteria();
  }, []);

  function startPolling() {
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await getScoringStatus();
        if (data.status === "scoring") {
          setScoring({ scored: data.scored, total: data.total });
        } else if (data.status === "done") {
          setScoring({ scored: data.scored, total: data.total, done: true });
          clearInterval(pollRef.current);
          // Clear after 3 seconds
          setTimeout(() => setScoring(null), 3000);
        } else {
          clearInterval(pollRef.current);
        }
      } catch {
        clearInterval(pollRef.current);
      }
    }, 1500);
  }

  // Resume polling if scoring was already in progress when this page mounts
  useEffect(() => {
    getScoringStatus().then(({ data }) => {
      if (data.status === "scoring") {
        setScoring({ scored: data.scored, total: data.total });
        startPolling();
      }
    }).catch(() => {});
    return () => clearInterval(pollRef.current);
  }, []);

  async function handleScrape() {
    setScraping(true);
    setScrapeResult(null);
    setScoring(null);
    clearInterval(pollRef.current);
    try {
      const { data } = await triggerScrape();
      setScrapeResult({ ok: true, ...data });
      startPolling();
    } catch (err) {
      const detail =
        err.response?.data?.detail ??
        `Scrape failed: could not reach backend (${err.message ?? "network error"}).`;
      setScrapeResult({ ok: false, detail });
    } finally {
      setScraping(false);
    }
  }

  const pct = scoring ? Math.round((scoring.scored / scoring.total) * 100) : 0;
  const canScrape = hasTitles && companies.length > 0;

  return (
    <div className="space-y-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <div className="flex flex-col items-end gap-1">
          {!hasTitles && (
            <p className="text-xs text-amber-500 dark:text-amber-400">
              Add at least one job title to enable scraping
            </p>
          )}
          {hasTitles && companies.length === 0 && (
            <p className="text-xs text-amber-500 dark:text-amber-400">
              Add at least one company to enable scraping
            </p>
          )}
        <button
          onClick={handleScrape}
          disabled={scraping || !canScrape}
          title={!hasTitles ? "Add job titles first" : !companies.length ? "Add companies first" : ""}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {scraping ? "Scraping…" : "Scrape & Score My Feed"}
        </button>
        </div>
      </div>

      {scrapeResult && (
        <div
          className={`text-sm rounded-lg px-4 py-3 ${
            scrapeResult.ok
              ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400"
              : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400"
          }`}
        >
          {scrapeResult.ok ? (
            <div className="space-y-1">
              <p>
              {scrapeResult.new_jobs > 0 ? (
                <>
                  <strong>{scrapeResult.new_jobs}</strong> new job{scrapeResult.new_jobs === 1 ? "" : "s"} added —{" "}
                  scoring your feed in the background.
                </>
              ) : scrapeResult.total_fetched > 0 ? (
                <>
                  No new listings found — <strong>{scrapeResult.total_fetched}</strong> job{scrapeResult.total_fetched === 1 ? "" : "s"} checked, all already in your feed.
                </>
              ) : scrapeResult.cached > 0 ? (
                <>
                  Your companies were all scraped recently —{" "}
                  {scrapeResult.cached === 1 ? "1 company" : `${scrapeResult.cached} companies`} served from cache. Feed is up to date.
                </>
              ) : (
                <>
                  No jobs found — the company slug may be incorrect, or they may not post on this platform.
                </>
              )}
              </p>
              {scrapeResult.no_results?.length > 0 && (
                <p className="text-xs text-amber-500 dark:text-amber-400">
                  No listings found for:{" "}
                  <span className="font-medium">
                    {scrapeResult.no_results.join(", ")}
                  </span>{" "}
                  — double-check those slugs or try the other platform.
                </p>
              )}
            </div>
          ) : (
            scrapeResult.detail
          )}
        </div>
      )}

      {scoring && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>
              {scoring.done
                ? `Scored ${scoring.scored} jobs`
                : `Scoring ${scoring.scored} of ${scoring.total} jobs…`}
            </span>
            <span>{pct}%</span>
          </div>
          <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                scoring.done ? "bg-green-500" : "bg-indigo-500"
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      <section>
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-1">
          Company Sources
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Add companies by their job board slug. Not sure which platform a company uses? Try both — each card links to the right URL. Slugs scraped recently by another user are served from cache, so no redundant calls.
        </p>
        <div className="mb-4">
          <Link
            to="/companies"
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium rounded border border-indigo-200 dark:border-indigo-700 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/30"
          >
            Browse Suggested Companies
          </Link>
        </div>
        <SectorPicker companies={companies} onRefresh={refreshCompanies} />
        <CompanySlugs companies={companies} onRefresh={refreshCompanies} />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-1">
          Match Criteria
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Claude scores each job 1–100 against these criteria. Jobs in your feed are
          pre-filtered by title and location, then ranked by score.
        </p>
        <SettingsForm onSave={refreshCriteria} />
      </section>
    </div>
  );
}
