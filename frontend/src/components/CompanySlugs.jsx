import { useState } from "react";
import { addCompany, deleteCompany } from "../api/client";

const SOURCES = ["greenhouse", "lever"];
const SOURCE_LABELS = { greenhouse: "Greenhouse", lever: "Lever" }

const SOURCE_HINTS = {
  greenhouse: {
    description: "Used by Stripe, Airbnb, Figma, and most large startups.",
    url: "boards.greenhouse.io/{slug}",
    href: "https://boards.greenhouse.io",
  },
  lever: {
    description: "Used by Netflix, Shopify, Atlassian, and others.",
    url: "jobs.lever.co/{slug}",
    href: "https://jobs.lever.co",
  },
};

function timeAgo(iso) {
  if (!iso) return null;
  const normalized = iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z";
  const diff = Math.floor((Date.now() - new Date(normalized)) / 1000);
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function CompanySlugs({ companies = [], onRefresh }) {
  const [newSlug, setNewSlug] = useState({ greenhouse: "", lever: "" });
  const [error, setError] = useState({ greenhouse: "", lever: "" });

  const bySource = (source) => companies.filter((c) => c.source === source);

  async function handleAdd(source) {
    const slug = newSlug[source].trim().toLowerCase();
    if (!slug) return;
    try {
      await addCompany(source, slug);
      setNewSlug((prev) => ({ ...prev, [source]: "" }));
      setError((prev) => ({ ...prev, [source]: "" }));
      onRefresh?.();
    } catch (err) {
      setError((prev) => ({
        ...prev,
        [source]: err.response?.data?.detail ?? "Failed to add.",
      }));
    }
  }

  async function handleDelete(id) {
    await deleteCompany(id);
    onRefresh?.();
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {SOURCES.map((source) => (
        <div key={source} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 sm:p-5">
          <div className="mb-3">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200">
              {SOURCE_LABELS[source]}
            </h3>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
              {SOURCE_HINTS[source].description}{" "}
              <a
                href={SOURCE_HINTS[source].href}
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-indigo-500"
              >
                {SOURCE_HINTS[source].url}
              </a>
            </p>
          </div>

          <ul className="space-y-2 mb-4">
            {bySource(source).length === 0 ? (
              <li className="text-sm text-gray-400 dark:text-gray-500 italic">None added yet.</li>
            ) : (
              bySource(source).map((c) => (
                <li key={c.id} className="flex items-center justify-between text-sm">
                  <div>
                    <span className="text-gray-800 dark:text-gray-200 font-medium">{c.slug}</span>
                    {c.last_scraped_at ? (
                      <span className="ml-2 text-xs text-gray-400 dark:text-gray-500">
                        scraped {timeAgo(c.last_scraped_at)}
                      </span>
                    ) : (
                      <span className="ml-2 text-xs text-amber-500">not scraped yet</span>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="text-xs px-2 py-0.5 rounded bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40"
                  >
                    Remove
                  </button>
                </li>
              ))
            )}
          </ul>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="company-slug"
              value={newSlug[source]}
              onChange={(e) =>
                setNewSlug((prev) => ({ ...prev, [source]: e.target.value }))
              }
              onKeyDown={(e) => e.key === "Enter" && handleAdd(source)}
              className="flex-1 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
            <button
              onClick={() => handleAdd(source)}
              className="text-sm px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              Add
            </button>
          </div>
          {error[source] && (
            <p className="text-xs text-red-500 mt-1">{error[source]}</p>
          )}
        </div>
      ))}
    </div>
  );
}
