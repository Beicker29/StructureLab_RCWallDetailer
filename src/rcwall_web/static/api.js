// Transport envelopes may be parsed; the canonical document always remains text.
export async function request(operation, data) {
  const response = await fetch(`/api/${operation}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw await response.json();
  return operation === "export" ? response.text() : response.json();
}

export function errorText(error) {
  if (error instanceof Error) {
    return "No se pudo completar la solicitud. Compruebe que el servidor local sigue activo.";
  }
  const names = {
    length_mm: "Longitud", thickness_mm: "Espesor", x_mm: "Coordenada X",
    y_mm: "Coordenada Y", diameter_mm: "Diámetro", project_id: "Identidad del proyecto",
    schema_version: "Versión del contrato", units: "Unidades",
  };
  return [error.message, ...(error.issues || []).map(
    (issue) => `${names[issue.path.at(-1)] || "Datos del proyecto"}: ${issue.message}`,
  )].join("\n");
}

export function downloadDocument(text) {
  const url = URL.createObjectURL(new Blob([text], { type: "application/json;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "proyecto.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
