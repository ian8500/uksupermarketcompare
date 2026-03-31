import { getJson } from "../../lib/api";
export default async function SavedListsPage() {
  const lists = await getJson<Array<{ id: number; name: string; items: string[] }>>("/saved-lists");
  return <div><h2 className="text-xl font-semibold">Saved Lists</h2><ul className="mt-2 space-y-2">{lists.map(l=> <li className="bg-white p-3 rounded border" key={l.id}><p className="font-medium">{l.name}</p><p className="text-sm text-slate-600">{l.items.join(", ")}</p></li>)}</ul></div>;
}
