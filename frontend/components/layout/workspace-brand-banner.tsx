import { CircuitLogo } from "@/components/ui/circuit-logo";

export function WorkspaceBrandBanner() {
  return (
    <footer className="workspace-brand-banner" aria-label="BI-DATA">
      <div className="banner-brand">
        <CircuitLogo size={56} />
        <div>
          <strong>BI-DATA</strong>
          <span>
            Inteligencia de negocios
            <br />y ciencia de datos
          </span>
        </div>
      </div>
      <div className="banner-message">
        <strong>Hacia la transformación digital</strong>
        <p>Convierte tus datos en conversaciones.</p>
      </div>
      <span className="banner-values">
        Analiza
        <br />
        Conecta
        <br />
        Transforma
      </span>
    </footer>
  );
}
