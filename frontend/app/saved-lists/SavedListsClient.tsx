"use client";

import { useMemo, useState } from "react";

import { ApiError, deleteJson } from "../../lib/api";

type SavedList = { id: number; name: string; items: string[] };

export default function SavedListsClient({ initialLists }: { initialLists: SavedList[] }) {
  const [lists, setLists] = useState(initialLists);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const hasLists = useMemo(() => lists.length > 0, [lists]);

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    setError(null);
    try {
      await deleteJson(`/saved-lists/${id}`);
      setLists((prev) => prev.filter((list) => list.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete this saved list.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Saved Lists</h2>
      {!hasLists ? (
        <p className="mt-3 rounded border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
          No saved lists yet. Create a basket first and save it to compare later.
        </p>
      ) : (
        <ul className="mt-2 space-y-2">
          {lists.map((list) => (
            <li className="rounded border bg-white p-3" key={list.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium">{list.name}</p>
                  <p className="text-sm text-slate-600">{list.items.join(", ")}</p>
                </div>
                <button
                  className="rounded border border-red-200 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={deletingId === list.id}
                  onClick={() => void handleDelete(list.id)}
                  type="button"
                >
                  {deletingId === list.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
