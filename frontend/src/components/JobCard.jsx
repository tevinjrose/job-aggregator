import { useState } from "react";
import { updateJobStatus } from "../api/client";

function scoreStyle(score) {
  if (score === null || score === undefined)
    return { bg: "bg-gray-100 dark:bg-gray-700", text: "text-gray-400 dark:text-gray-500", label: "—" };
  if (score >= 80) return { bg: "bg-green-100 dark:bg-green-900/40", text: "text-green-700 dark:text-green-400", label: score };
  if (score >= 60) return { bg: "bg-yellow-100 dark:bg-yellow-900/40", text: "text-yellow-700 dark:text-yellow-400", label: score };
  if (score >= 40) return { bg: "bg-orange-100 dark:bg-orange-900/40", text: "text-orange-700 dark:text-orange-400", label: score };
  return { bg: "bg-red-100 dark:bg-red-900/40", text: "text-red-600 dark:text-red-400", label: score };
}

function relativeDate(iso) {
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(iso).toLocaleDateString();
}

const SOURCE_COLORS = {
  greenhouse: "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400",
  lever: "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400",
};

export default function JobCard({ job, onRemove }) {
  const [status, setStatus] = useState(job.status);
  const [loading, setLoading] = useState(false);
  const style = scoreStyle(job.score);

  async function handleStatus(next) {
    const newStatus = status === next ? null : next;
    setLoading(true);
    try {
      await updateJobStatus(job.id, newStatus);
      setStatus(newStatus);
      if (newStatus === "dismissed" || newStatus !== null) {
        onRemove?.(job.id);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 sm:p-5 flex gap-3 sm:gap-4 hover:shadow-sm dark:hover:shadow-none transition-shadow">
      {/* Score badge */}
      <div className={`flex-shrink-0 w-14 h-14 rounded-xl flex flex-col items-center justify-center ${style.bg}`}>
        <span className={`text-lg font-bold leading-none ${style.text}`}>{style.label}</span>
        {job.score !== null && job.score !== undefined && (
          <span className={`text-[10px] leading-none mt-0.5 ${style.text} opacity-70`}>/100</span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{job.title}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              <span className="font-medium text-gray-700 dark:text-gray-300 capitalize">
                {job.company_slug}
              </span>
              {job.location && <> · {job.location}</>}
              {job.salary && (
                <span className="ml-2 text-green-700 dark:text-green-400 font-medium">{job.salary}</span>
              )}
            </p>
          </div>
          {/* Apply — hidden on mobile; lives in the action row instead */}
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex flex-shrink-0 text-sm px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
          >
            Apply →
          </a>
        </div>

        <div className="flex items-center gap-2 mt-2.5">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SOURCE_COLORS[job.source] ?? "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"}`}>
            {job.source}
          </span>
          <span className="text-xs text-gray-400 dark:text-gray-500">{relativeDate(job.posted_at)}</span>
          {job.is_stale && (
            <span className="text-xs text-amber-500 dark:text-amber-400">· may be closed</span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-3">
          <button
            disabled={loading}
            onClick={() => handleStatus("saved")}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              status === "saved"
                ? "bg-indigo-600 text-white border-indigo-600"
                : "border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-indigo-400 hover:text-indigo-600 dark:hover:border-indigo-500 dark:hover:text-indigo-400"
            }`}
          >
            Saved
          </button>
          <button
            disabled={loading}
            onClick={() => handleStatus("applied")}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              status === "applied"
                ? "bg-green-600 text-white border-green-600"
                : "border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-green-400 hover:text-green-600 dark:hover:border-green-500 dark:hover:text-green-400"
            }`}
          >
            Applied
          </button>
          {/* Apply — mobile only, sits alongside the status buttons */}
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="sm:hidden text-xs px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
          >
            Apply →
          </a>
          <button
            disabled={loading}
            onClick={() => handleStatus("dismissed")}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-600 text-gray-400 dark:text-gray-500 hover:border-red-300 dark:hover:border-red-700 hover:text-red-500 dark:hover:text-red-400 transition-colors ml-auto"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
