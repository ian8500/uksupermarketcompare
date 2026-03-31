import "./globals.css";
import Link from "next/link";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><header className="bg-white shadow-sm p-4 sticky top-0"><nav className="max-w-4xl mx-auto flex gap-4 text-sm font-medium"><Link href="/">Home</Link><Link href="/create-basket">Create Basket</Link><Link href="/saved-lists">Saved Lists</Link><Link href="/admin">Admin</Link></nav></header><main className="max-w-4xl mx-auto p-4">{children}</main></body></html>;
}
