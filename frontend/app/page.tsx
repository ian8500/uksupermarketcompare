import Link from "next/link";

const features = [
  "Live basket comparison across Tesco, Sainsbury's and Asda",
  "Transparent confidence labels for exact, close and substitute matches",
  "Own-brand savings estimate to reduce weekly spend",
];

export default function HomePage() {
  return (
    <section className="space-y-8">
      <div className="rounded-xl border bg-gradient-to-br from-slate-50 to-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">UK Grocery Intelligence</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">BasketCompare</h1>
        <p className="mt-3 max-w-2xl text-slate-600">
          Compare your full grocery basket in one place with pricing transparency, confidence scoring and own-brand substitution options.
        </p>
        <div className="mt-6 flex gap-3">
          <Link href="/create-basket" className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white">
            Start comparison
          </Link>
          <Link href="/saved-lists" className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700">
            View saved lists
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {features.map((feature) => (
          <article key={feature} className="rounded-lg border bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-900">Feature</h2>
            <p className="mt-2 text-sm text-slate-600">{feature}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
