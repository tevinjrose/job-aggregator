import { useEffect, useState } from "react";
import { getCriteria, saveCriteria } from "../api/client";

const FIELD_LABELS = {
  titles: "Job Titles",
  keywords: "Keywords",
  locations: "Locations",
  excluded_companies: "Excluded Companies",
};

function TagInput({ label, values, onChange }) {
  const [input, setInput] = useState("");

  function add() {
    const v = input.trim();
    if (v && !values.includes(v)) onChange([...values, v]);
    setInput("");
  }

  function remove(v) {
    onChange(values.filter((x) => x !== v));
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
      </label>
      <div className="flex flex-wrap gap-1.5 mb-2 min-h-[2rem]">
        {values.map((v) => (
          <span
            key={v}
            className="inline-flex items-center gap-1 text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-full"
          >
            {v}
            <button
              type="button"
              onClick={() => remove(v)}
              className="hover:text-indigo-900 dark:hover:text-indigo-100 font-bold"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          placeholder={`Add ${label.toLowerCase()}…`}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          className="flex-1 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        />
        <button
          type="button"
          onClick={add}
          className="text-sm px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
        >
          Add
        </button>
      </div>
    </div>
  );
}

export default function SettingsForm({ onSave }) {
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getCriteria().then((r) => setForm(r.data));
  }, []);

  function setList(field, values) {
    setForm((prev) => ({ ...prev, [field]: values }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await saveCriteria(form);
      setSaved(true);
      onSave?.();
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  }

  if (!form) return <p className="text-sm text-gray-400 dark:text-gray-500">Loading…</p>;

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-6">
      {Object.entries(FIELD_LABELS).map(([field, label]) => (
        <TagInput
          key={field}
          label={label}
          values={form[field] ?? []}
          onChange={(v) => setList(field, v)}
        />
      ))}

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Minimum Salary (optional)
        </label>
        <input
          type="number"
          value={form.min_salary ?? ""}
          onChange={(e) =>
            setForm((prev) => ({
              ...prev,
              min_salary: e.target.value ? parseInt(e.target.value) : null,
            }))
          }
          placeholder="e.g. 120000"
          className="text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 rounded px-2 py-1 w-48 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          id="exclude-onsite"
          type="checkbox"
          checked={form.exclude_onsite_outside_major_cities}
          onChange={(e) =>
            setForm((prev) => ({
              ...prev,
              exclude_onsite_outside_major_cities: e.target.checked,
            }))
          }
          className="rounded border-gray-300 dark:border-gray-600 text-indigo-600"
        />
        <label htmlFor="exclude-onsite" className="text-sm text-gray-700 dark:text-gray-300">
          Exclude on-site roles outside major cities
        </label>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save Criteria"}
        </button>
        {saved && <span className="text-sm text-green-600 dark:text-green-400">Saved!</span>}
      </div>
    </form>
  );
}
