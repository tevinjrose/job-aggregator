import { useEffect, useState } from "react";
import CompanyDirectoryPicker from "../components/CompanyDirectoryPicker";
import CompanySlugs from "../components/CompanySlugs";
import { getCompanies } from "../api/client";

export default function Companies() {
  const [companies, setCompanies] = useState([]);

  async function refreshCompanies() {
    const { data } = await getCompanies();
    setCompanies(data);
  }

  useEffect(() => {
    refreshCompanies();
  }, []);

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Companies</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Browse suggested companies or add a manual slug. Use this page to manage what gets scraped.
        </p>
      </section>

      <CompanyDirectoryPicker companies={companies} onRefresh={refreshCompanies} />

      <section>
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-1">
          Manual Slugs
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          If a company is missing from suggestions, add it directly by slug.
        </p>
        <CompanySlugs companies={companies} onRefresh={refreshCompanies} />
      </section>
    </div>
  );
}
