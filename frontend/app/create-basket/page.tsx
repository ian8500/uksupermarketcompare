"use client";
import { useState } from "react";
import { ApiError, postJson } from "../../lib/api";
type Resp = { basket_id: number };
export default function CreateBasketPage() {
  const [items, setItems] = useState("semi skimmed milk 2L\nheinz baked beans\npenne pasta 500g");
  const [retailers, setRetailers] = useState<string[]>(["tesco", "sainsburys", "asda"]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lines = items.split("\n").map((i) => i.trim()).filter(Boolean);
  const canSubmit = lines.length > 0 && retailers.length > 0 && !isLoading;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setError(null);
    setIsLoading(true);
    try {
      const data = await postJson<Resp>("/baskets/compare", { items: lines, retailers });
      window.location.href = `/baskets/${data.basket_id}?retailers=${retailers.join(",")}`;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to compare basket right now.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Create Basket</h2>
      <p className="text-sm text-slate-600">Paste one item per line, then choose retailers to generate a professional comparison report.</p>

      <textarea className="min-h-48 w-full rounded border p-3" value={items} onChange={(e) => setItems(e.target.value)} />

      <div className="space-y-2">
        <p className="text-sm font-medium text-slate-700">Retailers</p>
        <div className="flex gap-4">
          {["tesco", "sainsburys", "asda"].map((r) => (
            <label key={r} className="text-sm capitalize">
              <input type="checkbox" checked={retailers.includes(r)} onChange={() => setRetailers((p) => (p.includes(r) ? p.filter((x) => x !== r) : [...p, r]))} /> {r}
            </label>
          ))}
        </div>
      </div>

      {error ? <p className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
      {!canSubmit ? <p className="text-xs text-amber-700">Add at least one basket line and select at least one retailer.</p> : null}

      <button className="rounded bg-slate-900 px-4 py-2 text-white disabled:cursor-not-allowed disabled:bg-slate-400" disabled={!canSubmit} onClick={handleSubmit}>
        {isLoading ? "Comparing..." : "Compare Basket"}
      </button>
    </div>
  );
}
