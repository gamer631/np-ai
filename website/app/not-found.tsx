import Link from "next/link";

export default function NotFound() {
  return (
    <main className="not-found">
      <p className="kicker">404 / NOT FOUND</p>
      <h1>This page is<br /><span>off the map.</span></h1>
      <p>The page may have moved or may not exist.</p>
      <Link className="button button-primary" href="/">Return to NIL.ai</Link>
    </main>
  );
}
