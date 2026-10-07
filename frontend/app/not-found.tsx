import Link from "next/link";

import { Brand } from "@/components/ui/brand";

export default function NotFound() {
  return (
    <main className="not-found-page">
      <Brand />
      <section aria-labelledby="not-found-title">
        <span className="not-found-code">404</span>
        <h1 id="not-found-title">No encontramos esta página</h1>
        <p>
          La dirección puede haber cambiado o contener un error. Vuelve al panel para
          continuar.
        </p>
        <Link className="button button-primary" href="/">
          Volver al panel
        </Link>
      </section>
    </main>
  );
}
