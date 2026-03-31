import { getJson } from "../../lib/api";
export default async function AdminPage() {
  const rows = await getJson<Array<{ query: string; confidence: string; score: number }>>("/admin/matches");
  return <div><h2 className="text-xl font-semibold">Admin / Match Debug</h2><pre className="bg-slate-900 text-slate-100 p-3 rounded mt-3 overflow-auto text-xs">{JSON.stringify(rows, null, 2)}</pre></div>;
}
