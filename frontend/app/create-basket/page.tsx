"use client";
import { useState } from "react";
import { postJson } from "../../lib/api";
type Resp = { basket_id: number };
export default function CreateBasketPage() {
  const [items, setItems] = useState("semi skimmed milk 2L\nheinz baked beans\npenne pasta 500g");
  const [retailers, setRetailers] = useState<string[]>(["tesco", "sainsburys", "asda"]);
  return <div className="space-y-3"><h2 className="text-xl font-semibold">Create Basket</h2><textarea className="w-full min-h-48 p-3 rounded border" value={items} onChange={(e)=>setItems(e.target.value)} /><div className="flex gap-2">{['tesco','sainsburys','asda'].map((r)=><label key={r} className="text-sm"><input type="checkbox" checked={retailers.includes(r)} onChange={()=>setRetailers((p)=>p.includes(r)?p.filter(x=>x!==r):[...p,r])}/> {r}</label>)}</div><button className="bg-slate-900 text-white px-4 py-2 rounded" onClick={async()=>{const data=await postJson<Resp>("/baskets/compare",{items:items.split("\n").filter(Boolean),retailers});window.location.href=`/baskets/${data.basket_id}`;}}>Compare Basket</button></div>;
}
