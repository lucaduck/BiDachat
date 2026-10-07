export function documentFailure(errorCode: string | null) {
  if (errorCode === "image_model_not_configured")
    return "Configura OLLAMA_MODEL con un modelo visual para procesar la imagen.";
  if (errorCode === "image_processing_failed")
    return "No se pudo describir la imagen. Comprueba que Ollama y el modelo visual estén disponibles.";
  if (errorCode === "embedding_not_configured")
    return "Falta configurar el proveedor de embeddings en el backend.";
  if (errorCode === "embedding_provider_failed")
    return "El proveedor de embeddings no respondió. Revisa su configuración y disponibilidad.";
  if (errorCode === "file_read_failed") return "No se pudo leer el archivo almacenado.";
  return "No se pudo procesar el documento. Comprueba que tenga texto legible y que el proveedor de embeddings esté disponible.";
}
