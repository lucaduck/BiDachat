const MAX_FILE_SIZE = 20 * 1024 * 1024;
const MAX_IMAGE_SIZE = 4 * 1024 * 1024;
const IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "webp"];
const ALLOWED_EXTENSIONS = ["pdf", "docx", "txt", "csv", ...IMAGE_EXTENSIONS];

export function validateDocument(file: File): string | null {
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (!extension || !ALLOWED_EXTENSIONS.includes(extension))
    return "Selecciona un archivo PDF, DOCX, TXT, CSV, PNG, JPEG o WebP.";
  if (file.size === 0) return "El archivo está vacío.";
  if (IMAGE_EXTENSIONS.includes(extension) && file.size > MAX_IMAGE_SIZE)
    return "La imagen supera el máximo de 4 MB.";
  if (file.size > MAX_FILE_SIZE) return "El archivo supera el máximo de 20 MB.";
  return null;
}
