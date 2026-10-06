import { CircuitLogo } from "./circuit-logo";

export function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark brand-circuit">
        <CircuitLogo priority />
      </span>
      <span className="brand-wordmark">
        <strong>BIDACHAT</strong>
        <span>Impulsado por BI-DATA</span>
      </span>
    </div>
  );
}
