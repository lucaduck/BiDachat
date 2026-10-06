import { Button } from "@/components/ui/button";
export function WizardActions({
  step,
  busy,
  onBack,
}: Readonly<{ step: number; busy: boolean; onBack: () => void }>) {
  return (
    <div className="wizard-actions">
      <Button type="button" variant="secondary" onClick={onBack} disabled={busy}>
        {step === 0 ? "Cancelar" : "Anterior"}
      </Button>
      <Button type="submit" isLoading={busy}>
        {step === 2 ? "Guardar y continuar" : "Siguiente paso"}
      </Button>
    </div>
  );
}
