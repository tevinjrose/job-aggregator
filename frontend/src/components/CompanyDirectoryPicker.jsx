import { useEffect, useMemo, useState } from "react";
import { addCompany, getCompanyDirectory } from "../api/client";

const MAX_COMPANIES = 20;
const SOURCE_LABELS = { greenhouse: "Greenhouse", lever: "Lever" };

export default function CompanyDirectoryPicker({ companies = [], onRefresh }) {
  const [directory, setDirectory] = useState([]);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getCompanyDirectory()
      .then(({ data }) => setDirectory(data))
      .catch(() => setDirectory([]));
  }, []);

  const selected = useMemo(
    () => new Set(companies.map((c) => `${c.source}:${c.slug}`)),
    [companies]
  );

  const atCap = companies.length >= MAX_COMPANIES;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return directory
      .filter((item) => source === "all" || item.source === source)
      .filter((item) => {
        if (!q) return true;
        return item.label.toLowerCase().includes(q) || item.slug.toLowerCase().includes(q);
      })
      .slice(0, 40);
  }, [directory, query, source]);

  async function handleAdd(item) {
    if (atCap || busy) return;
    setBusy(`${item.source}:${item.slug}`);
    setError("");
    try {
      await addCompany(item.source, item.slug);
      onRefresh?.();
    } catch (err) {
      setError(err.response?.data?.detail ?? "Failed to add company.");
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="mb-6 border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800">
      <div className="flex flex-col md:flex-row gap-2 md:items-center md:justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-800 dark:text-gray-200">Company Directory</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Browse known companies and add them in one click.
          </p>
        </div>
        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 w-fit">
          {companies.length}/{MAX_COMPANIES} companies
        </span>
      </div>

      <div className="flex flex-col md:flex-row gap-2 mb-3">
        <input
          type="text"
          placeholder="Search by company or slug"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        />
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          <option value="all">All Sources</option>
          <option value="greenhouse">Greenhouse</option>
          <option value="lever">Lever</option>
        </select>
      </div>

      {atCap && (
        <p className="text-xs text-red-500 dark:text-red-400 mb-2">
          You've reached the {MAX_COMPANIES}-company limit. Remove one to add another.
        </p>
      )}
      {error && <p className="text-xs text-red-500 dark:text-red-400 mb-2">{error}</p>}

      <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {filtered.map((item) => {
          const key = `${item.source}:${item.slug}`;
          const alreadyAdded = selected.has(key);
          const isBusy = busy === key;
          return (
            <li
              key={key}
              className="border border-gray-200 dark:border-gray-700 rounded px-3 py-2 flex items-center justify-between gap-3"
            >
              <div className="min-w-0">
                <p className="text-sm text-gray-800 dark:text-gray-200 truncate">{item.label}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {item.slug} · {SOURCE_LABELS[item.source]}
                </p>
              </div>
              <button
                disabled={alreadyAdded || atCap || isBusy}
                onClick={() => handleAdd(item)}
                className={`text-xs px-2 py-1 rounded ${
                  alreadyAdded
                    ? "bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400 cursor-default"
                    : "bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                }`}
              >
                {isBusy ? "Adding..." : alreadyAdded ? "Added" : "Add"}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
