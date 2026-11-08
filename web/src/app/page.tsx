import { ApiStatusBadge } from "@/components/ApiStatusBadge";

export default function Home() {
  return (
    <main className="home">
      <h1>Planetes</h1>
      <p className="tagline">
        Type sky coordinates and watch real NASA SPHEREx infrared images of that patch play as a time-lapse.
      </p>
      <ApiStatusBadge />
    </main>
  );
}
