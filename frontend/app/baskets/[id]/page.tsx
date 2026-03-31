import { getJson } from "../../../lib/api";
type ComparisonResponse = {
  basket_id: number;
  cheapest_overall_basket: number;
  cheapest_single_store_basket: Record<string, number>;
  own_brand_savings: number;
  results: Array<{
    query: string;
    matches: Array<{
      product_name: string;
      supermarket: string;
      price: number;
      confidence: "exact" | "close" | "substitute";
      uncertainty: string | null;
    }>;
  }>;
};

const toneMap: Record<string, string> = {
  exact: "bg-emerald-100 text-emerald-700",
  close: "bg-amber-100 text-amber-700",
  substitute: "bg-violet-100 text-violet-700",
};

export default async function BasketResultsPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams: { retailers?: string };
}) {
  const retailers = searchParams.retailers || "tesco,sainsburys,asda";
  const basket = await getJson<{ id: number; name: string; items: string[] }>(`/baskets/${params.id}`);
  const comparison = await getJson<ComparisonResponse>(`/baskets/${params.id}/comparison?retailers=${encodeURIComponent(retailers)}`);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Basket Results: {basket.name}</h2>
        <p className="mt-1 text-sm text-slate-600">Retailers: {retailers.split(",").join(", ")}</p>
      </div>

      <section className="grid gap-3 md:grid-cols-3">
        <article className="rounded border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Cheapest overall</p>
          <p className="mt-2 text-2xl font-bold">£{comparison.cheapest_overall_basket.toFixed(2)}</p>
        </article>
        <article className="rounded border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Own-brand savings</p>
          <p className="mt-2 text-2xl font-bold">£{comparison.own_brand_savings.toFixed(2)}</p>
        </article>
        <article className="rounded border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Single-store totals</p>
          <ul className="mt-2 text-sm text-slate-700">
            {Object.entries(comparison.cheapest_single_store_basket).map(([store, total]) => (
              <li key={store} className="capitalize">
                {store}: £{total.toFixed(2)}
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="space-y-3">
        {comparison.results.map((row) => (
          <article key={row.query} className="rounded border bg-white p-4">
            <h3 className="font-semibold text-slate-900">{row.query}</h3>
            <ul className="mt-3 space-y-2">
              {row.matches.map((match) => (
                <li key={`${row.query}-${match.supermarket}-${match.product_name}`} className="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-200 p-3">
                  <div>
                    <p className="font-medium">{match.product_name}</p>
                    <p className="text-xs text-slate-500">{match.supermarket}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">£{match.price.toFixed(2)}</span>
                    <span className={`rounded px-2 py-1 text-xs font-semibold ${toneMap[match.confidence]}`}>{match.confidence}</span>
                  </div>
                  {match.uncertainty ? <p className="w-full text-xs text-amber-700">Note: {match.uncertainty}</p> : null}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </section>
    </div>
  );
}
