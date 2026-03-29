import { useEffect, useState } from "react";
import { getSectors, addSector, removeSector } from "../api/client";

const MAX_COMPANIES = 20;

export default function SectorPicker({ companies = [], onRefresh }) {
  const [sectors, setSectors] = useState({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    getSectors()
      .then(({ data }) => setSectors(data))
      .finally(() => setLoading(false));
  }, []);

  const atCap = companies.length >= MAX_COMPANIES;

  function sectorStatus(name) {
    const slugs = sectors[name] ?? [];
    if (!slugs.length) return { added: 0, total: 0, done: false, partial: false };
    const added = slugs.filter(({ source, slug }) =>
      companies.some((c) => c.source === source && c.slug === slug)
    ).length;
    return {
      added,
      total: slugs.length,
      done: added === slugs.length,
      partial: added > 0 && added < slugs.length,
    };
  }

  async function handleToggle(name) {
    setBusy(name);
    try {
      const { done, partial } = sectorStatus(name);
      if (done || (partial && atCap)) {
        await removeSector(name);
      } else {
        await addSector(name);
      }
      onRefresh?.();
    } catch {
      // ignore
    } finally {
      setBusy(null);
    }
  }

  if (loading) return null;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Not sure where to start? Pick a sector to auto-add companies:
        </p>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          atCap
            ? "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
            : "bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
        }`}>
          {companies.length}/{MAX_COMPANIES} companies
        </span>
      </div>

      {atCap && (
        <p className="text-xs text-red-500 dark:text-red-400 mb-3">
          You've reached the {MAX_COMPANIES}-company limit. Remove some companies to add new sectors.
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {Object.entries(sectors).map(([name, companies_]) => {
          const { added, total, done, partial } = sectorStatus(name);
          const isBusy = busy === name;
          const locked = atCap && !done && !partial;

          return (
            <button
              key={name}
              onClick={() => !isBusy && !locked && handleToggle(name)}
              disabled={isBusy || locked}
              title={
                locked
                  ? `Company limit reached (${MAX_COMPANIES} max)`
                  : done
                  ? "Click to remove these companies"
                  : partial
                  ? atCap
                    ? `${added}/${total} added — at company limit, click to remove`
                    : `${added}/${total} added — click to add remaining`
                  : `Add ${total} companies`
              }
              className={`text-sm px-3 py-1.5 rounded-full border font-medium transition-all ${
                done
                  ? "border-green-500 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 hover:border-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 dark:hover:text-red-400"
                  : partial
                  ? "border-amber-400 text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 hover:border-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                  : locked
                  ? "border-gray-200 dark:border-gray-700 text-gray-400 dark:text-gray-600 cursor-not-allowed opacity-50"
                  : "border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-400"
              }`}
            >
              {isBusy ? "…" : done ? `✓ ${name}` : name}
              {!done && !isBusy && (
                <span className={`ml-1.5 text-xs ${partial ? "text-amber-500 dark:text-amber-400 font-semibold" : "text-gray-400 dark:text-gray-500"}`}>
                  {partial ? `${added}/${total}` : total}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
