import { getJson } from "../../../lib/api";
export default async function BasketResultsPage({ params }: { params: { id: string } }) {
  const basket = await getJson<{ id: number; name: string; items: string[] }>(`/baskets/${params.id}`);
  return <div><h2 className="text-xl font-semibold">Basket Results: {basket.name}</h2><ul className="list-disc ml-5 mt-2">{basket.items.map((i) => <li key={i}>{i}</li>)}</ul><p className="mt-4 text-sm text-amber-700">Comparison uncertainty labels appear when pack sizes or product types differ.</p></div>;
}
