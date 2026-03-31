import { getJson } from "../../lib/api";
import SavedListsClient from "./SavedListsClient";

export default async function SavedListsPage() {
  const lists = await getJson<Array<{ id: number; name: string; items: string[] }>>("/saved-lists");
  return <SavedListsClient initialLists={lists} />;
}
