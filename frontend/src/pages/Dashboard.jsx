import { useState } from "react";
import JobFeed from "../components/JobFeed";

const TABS = [
  { id: "feed", label: "Feed" },
  { id: "saved", label: "Saved" },
  { id: "applied", label: "Applied" },
];

export default function Dashboard() {
  const [tab, setTab] = useState("feed");

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">JobRadar</h1>
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                tab === t.id
                  ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      <JobFeed tab={tab} />
    </div>
  );
}
