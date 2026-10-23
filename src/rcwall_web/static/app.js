import { downloadDocument, errorText, request } from "./api.js";
import {
  acceptProject, hasUnsavedChanges, invalidateRequests, isCurrent, markDownloaded,
  scheduleEdit, selectedConfig, selectedGeometry, state,
} from "./state.js";
import { createViewer } from "./svg.js";

const $ = (id) => document.getElementById(id);
const status = (message) => { $("status").textContent = message; };
const viewer = createViewer($("canvas"), $("scene"), $("zoom-label"), (key) => {
  state.selection = key;
  draw();
});

function showError(error) {
  $("errors").textContent = errorText(error);
  $("errors").hidden = false;
}

function options(element, items, selected) {
  element.replaceChildren(...items.map((item, index) => {
    const option = document.createElement("option");
    option.value = index;
    option.textContent = item.label;
    return option;
  }));
  element.value = selected;
  element.disabled = !items.length;
}

function properties(element, pairs) {
  element.replaceChildren();
  for (const [label, value] of pairs) {
    const term = document.createElement("dt");
    const definition = document.createElement("dd");
    term.textContent = label;
    definition.textContent = value;
    element.append(term, definition);
  }
}

function beforeUnload(event) {
  if (hasUnsavedChanges()) {
    event.preventDefault();
    event.returnValue = "";
  }
}

function syncControls() {
  const rectangular = selectedGeometry()?.rectangular;
  $("export").disabled = !state.current || state.pending || state.busy;
  $("geometry").disabled = !state.current?.geometries.length || state.pending || state.busy;
  $("configuration").disabled = !selectedGeometry()?.configurations.length || state.busy;
  for (const name of ["length", "thickness", "apply"]) {
    $(name).disabled = !rectangular || state.busy;
  }
  $("discard").disabled = !state.pending || state.busy;
  $("new").disabled = state.busy;
  $("file").disabled = state.busy;
  $("create-submit").disabled = state.busy;
  window.removeEventListener("beforeunload", beforeUnload);
  if (hasUnsavedChanges()) window.addEventListener("beforeunload", beforeUnload);
  $("save-state").textContent = !state.current ? "" : hasUnsavedChanges()
    ? "Cambios sin exportar" : "Versión recuperable del archivo importado o de la descarga iniciada";
}

function updateReinforcementNote() {
  const config = selectedConfig();
  $("reinforcement-note").textContent = config
    ? `${config.bars.length} barras explícitas. ${config.pending} distribuciones pendientes de resolver. ${config.graphics.warning}`
    : "La geometría se conserva, pero este prototipo solo dibuja rectángulos.";
  // Includes reinforcement declarations in alternative configurations.
  $("geometry-warning").hidden = !selectedGeometry()?.has_reinforcement;
}

function updatePanel() {
  const geometry = selectedGeometry();
  for (const name of ["length", "thickness"]) {
    $(name).value = geometry?.dimensions?.[name] || "";
  }
  options($("configuration"), geometry?.configurations || [], state.configIndex);
  properties($("origin"), geometry?.rectangular
    ? [["X (mm)", geometry.dimensions.x], ["Y (mm)", geometry.dimensions.y]]
    : [["Origen", "Sin rectángulo seleccionado"]]);
  updateReinforcementNote();
  syncControls();
}

function inspect() {
  const geometry = selectedGeometry();
  const bar = selectedConfig()?.bars[state.selection];
  const wall = state.selection === "wall" && geometry?.rectangular;
  $("selection-type").textContent = wall ? "CONTORNO SELECCIONADO"
    : bar ? "BARRA SELECCIONADA" : "SIN SELECCIÓN";
  $("selection-title").textContent = wall ? "Muro rectangular"
    : bar ? "Barra explícita" : "Explore la sección";
  $("selection-help").textContent = state.selection === null
    ? "Seleccione el contorno o una barra para consultar sus datos declarados."
    : "Valores declarados, sin redondeo gráfico.";
  properties($("properties"), wall ? [
    ["Longitud (mm)", geometry.dimensions.length],
    ["Espesor (mm)", geometry.dimensions.thickness],
    ["Origen X (mm)", geometry.dimensions.x],
    ["Origen Y (mm)", geometry.dimensions.y],
  ] : bar ? [
    ["Identificador declarado", bar.id],
    ["Posición X (mm)", bar.x],
    ["Posición Y (mm)", bar.y],
    ["Diámetro (mm)", bar.diameter],
  ] : []);
}

function draw() {
  $("empty").hidden = Boolean(state.current);
  viewer.draw(selectedConfig()?.graphics, state.selection);
  inspect();
}

function fit() { viewer.fit(selectedConfig()?.graphics.bounds); }

function install(data, source = "edit") {
  acceptProject(data, source);
  $("errors").hidden = true;
  options($("geometry"), data.geometries, state.geometryIndex);
  updatePanel();
  draw();
  if (source !== "edit") fit();
  status("Datos canónicos validados. Esto no constituye aprobación del detallado estructural.");
}

async function edit(ticket) {
  if (!state.current || !isCurrent(ticket)) return;
  try {
    const data = await request("edit", {
      document: state.current.document,
      index: state.geometryIndex,
      length: $("length").value,
      thickness: $("thickness").value,
    });
    if (isCurrent(ticket)) install(data);
  } catch (error) {
    if (isCurrent(ticket)) {
      showError(error);
      status("Entrada no aceptada. Se mantiene el último dibujo válido.");
    }
  }
}

function inputChanged() {
  scheduleEdit(edit);
  syncControls();
  status("Cambios pendientes de validación de datos…");
}

$("length").addEventListener("input", inputChanged);
$("thickness").addEventListener("input", inputChanged);
$("dimensions").onsubmit = (event) => {
  event.preventDefault();
  state.pending = true;
  syncControls();
  edit(invalidateRequests());
};
$("discard").onclick = () => {
  invalidateRequests();
  install(state.current);
  status("Cambios descartados por solicitud. Se recuperaron los valores aceptados.");
};
$("geometry").onchange = () => {
  invalidateRequests();
  state.geometryIndex = Number($("geometry").value);
  state.configIndex = 0;
  state.selection = null;
  $("errors").hidden = true;
  updatePanel();
  draw();
  fit();
};
$("configuration").onchange = () => {
  state.configIndex = Number($("configuration").value);
  state.selection = null;
  draw();
  fit();
  updateReinforcementNote();
};
$("zoom-in").onclick = () => viewer.zoom(0.8);
$("zoom-out").onclick = () => viewer.zoom(1.25);
$("fit").onclick = fit;

function confirmReplacement() {
  return !state.current || window.confirm(
    "¿Reemplazar el proyecto abierto? Se perderán sus cambios no exportados y entradas pendientes. Exporte antes los datos que desee conservar.",
  );
}

function openCreate() {
  // Freeze validation so cancel/escape cannot accept a late edit response.
  invalidateRequests();
  $("create-error").textContent = "";
  $("create-dialog").showModal();
}
$("new").onclick = openCreate;
$("empty-new").onclick = openCreate;
function cancelCreation() {
  // Invalidate synchronously; the dialog's close event is queued by the browser.
  invalidateRequests();
  state.busy = false;
  syncControls();
}
$("cancel-create").onclick = () => {
  cancelCreation();
  $("create-dialog").close();
};
$("create-dialog").addEventListener("cancel", cancelCreation);
$("create-dialog").addEventListener("close", () => {
  cancelCreation();
});

$("create-form").onsubmit = async (event) => {
  event.preventDefault();
  if (!confirmReplacement()) return;
  const ticket = invalidateRequests();
  state.busy = true;
  syncControls();
  try {
    const data = await request("create", Object.fromEntries(new FormData(event.target)));
    if (!isCurrent(ticket)) return;
    install(data, "create");
    $("create-dialog").close();
  } catch (error) {
    if (isCurrent(ticket)) $("create-error").textContent = errorText(error);
  } finally {
    if (isCurrent(ticket)) {
      state.busy = false;
      syncControls();
    }
  }
};

$("file").onchange = async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file || !confirmReplacement()) return;
  const ticket = invalidateRequests();
  state.busy = true;
  syncControls();
  try {
    if (file.size > 2 * 1024 * 1024) throw { message: "El archivo supera 2 MiB." };
    const data = await request("import", { document: await file.text() });
    if (isCurrent(ticket)) install(data, "import");
  } catch (error) {
    if (isCurrent(ticket)) showError(error);
  } finally {
    if (isCurrent(ticket)) {
      state.busy = false;
      syncControls();
    }
  }
};

$("export").onclick = async () => {
  if (!state.current || state.pending || state.busy) return;
  const document = state.current.document;
  const generation = state.generation;
  try {
    const text = await request("export", { document });
    downloadDocument(text);
    markDownloaded(document, generation);
    syncControls();
    status("Descarga JSON iniciada. Compruebe que el navegador guardó el archivo.");
  } catch (error) {
    showError(error);
  }
};
