import { useEffect, useState } from "react";
import { getJobs } from "../api/client";
import JobCard from "./JobCard";

export default function JobFeed({ tab }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getJobs(tab)
      .then((r) => setJobs(r.data))
      .catch(() => setError("Failed to load jobs."))
      .finally(() => setLoading(false));
  }, [tab]);

  function handleRemove(id) {
    setJobs((prev) => prev.filter((j) => j.id !== id));
  }

  if (loading)
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />
        ))}
      </div>
    );

  if (error)
    return <p className="text-sm text-red-500">{error}</p>;

  if (jobs.length === 0)
    return (
      <div className="text-center py-16 text-gray-400 dark:text-gray-500">
        <p className="text-lg font-medium">No jobs here yet.</p>
        {tab === "feed" && (
          <p className="text-sm mt-1">
            Go to{" "}
            <span className="font-medium text-gray-500 dark:text-gray-400">
              Settings → Scrape & Score My Feed
            </span>{" "}
            to pull in jobs.
          </p>
        )}
      </div>
    );

  return (
    <div className="space-y-3">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} onRemove={handleRemove} />
      ))}
    </div>
  );
}
