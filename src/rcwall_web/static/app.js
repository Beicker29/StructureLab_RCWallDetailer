"use strict";
// Canonical JSON is opaque text. Never parse it into JavaScript numbers.
const $ = (id) => document.getElementById(id);
let current = null, geometryIndex = 0, configIndex = 0, selection = null;
let revision = 0, timer, dirty = false, camera = [-100, -300, 1200, 700], baseWidth = 1200;
const canvas = $("canvas"), scene = $("scene");
function status(message) { $("status").textContent = message; }
function errorText(error) {
  if (error instanceof Error) return "No se pudo completar la solicitud. Compruebe que el servidor local sigue activo.";
  const names = {length_mm:"longitud",thickness_mm:"espesor",x_mm:"coordenada X",y_mm:"coordenada Y",diameter_mm:"diámetro",project_id:"identidad del proyecto",schema_version:"versión del contrato",units:"unidades"};
  return [error.message, ...(error.issues || []).map(i => `${names[i.path.at(-1)] || "Datos del proyecto"}: ${i.message}`)].join("\n");
}
function showError(error) { $("errors").textContent = errorText(error); $("errors").hidden = false; }
async function request(path, data) {
  const response = await fetch(`/api/${path}`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)});
  if (!response.ok) throw await response.json();
  return path === "export" ? response.text() : response.json();
}
function selectedGeometry() { return current?.geometries[geometryIndex]; }
function selectedConfig() { return selectedGeometry()?.configurations[configIndex]; }
function options(element, items, selected) {
  element.replaceChildren(...items.map((item, i) => { const option = document.createElement("option"); option.value = i; option.textContent = item.label; return option; }));
  element.value = selected; element.disabled = !items.length;
}
function properties(element, pairs) {
  element.replaceChildren();
  for (const [label, value] of pairs) { const dt = document.createElement("dt"), dd = document.createElement("dd"); dt.textContent = label; dd.textContent = value; element.append(dt, dd); }
}
function install(data, reset = false) {
  current = data; dirty = false; $("discard").disabled = true; $("export").disabled = false; $("errors").hidden = true;
  if (reset) { geometryIndex = Math.max(0, data.geometries.findIndex(g => g.rectangular)); configIndex = 0; selection = null; }
  options($("geometry"), data.geometries, geometryIndex);
  updatePanel(); draw(); if (reset) fit();
  status("Proyecto validado. Los valores canónicos se conservan en milímetros.");
}
function updatePanel() {
  const geo = selectedGeometry();
  for (const key of ["length", "thickness"]) { $(key).disabled = !geo?.rectangular; $(key).value = geo?.dimensions?.[key] || ""; }
  $("apply").disabled = !geo?.rectangular;
  options($("configuration"), geo?.configurations || [], configIndex);
  properties($("origin"), geo?.rectangular ? [["X (mm)", geo.dimensions.x], ["Y (mm)", geo.dimensions.y]] : [["Origen", "Sin rectángulo seleccionado"]]);
  updateReinforcementNote();
}
function updateReinforcementNote() {
  const config = selectedConfig();
  $("reinforcement-note").textContent = config ? `${config.bars.length} barras explícitas. ${config.pending} distribuciones pendientes de resolver. ${config.graphics.warning}` : "La geometría se conserva, pero este prototipo solo dibuja rectángulos.";
}
function inspect() {
  const geo = selectedGeometry(), bar = selectedConfig()?.bars[selection];
  $("selection-type").textContent = selection === "wall" ? "CONTORNO SELECCIONADO" : bar ? "BARRA SELECCIONADA" : "SIN SELECCIÓN";
  $("selection-title").textContent = selection === "wall" ? "Muro rectangular" : bar ? "Barra explícita" : "Explore la sección";
  $("selection-help").textContent = selection === null ? "Seleccione el contorno o una barra para consultar sus datos declarados." : "Valores declarados, sin redondeo gráfico.";
  properties($("properties"), selection === "wall" && geo?.rectangular ? [["Longitud (mm)", geo.dimensions.length], ["Espesor (mm)", geo.dimensions.thickness], ["Origen X (mm)", geo.dimensions.x], ["Origen Y (mm)", geo.dimensions.y]] : bar ? [["Identificador declarado", bar.id], ["Posición X (mm)", bar.x], ["Posición Y (mm)", bar.y], ["Diámetro (mm)", bar.diameter]] : []);
}
function shape(tag, attrs, key, label) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([name, value]) => node.setAttribute(name, value));
  node.setAttribute("class", `${tag === "rect" ? "wall-shape" : "bar-shape"}${selection === key ? " selected" : ""}`);
  node.setAttribute("tabindex", "0"); node.setAttribute("role", "button"); node.setAttribute("aria-label", label);
  const choose = () => { selection = key; draw(); };
  node.addEventListener("click", e => {e.stopPropagation(); choose();});
  node.addEventListener("keydown", e => {if (e.key === "Enter" || e.key === " ") {e.preventDefault(); choose();}});
  scene.append(node);
}
function draw() {
  scene.replaceChildren(); const config = selectedConfig();
  $("empty").hidden = Boolean(current);
  if (config?.graphics.rectangle) {shape("rect", config.graphics.rectangle, "wall", "Seleccionar contorno del muro"); config.graphics.circles.forEach((circle, i) => shape("circle", circle, i, `Seleccionar barra ${i+1}`));}
  inspect();
}
function cameraChanged() {canvas.setAttribute("viewBox", camera.join(" ")); $("zoom-label").textContent = `${Math.round(baseWidth / camera[2] * 100)} %`;}
function fit() {
  const bounds = selectedConfig()?.graphics.bounds || [0, 0, 1000, 200];
  const width = Math.max(bounds[2] * 1.3, 1), height = Math.max(bounds[3] * 1.8, width * .55);
  camera = [bounds[0] + bounds[2]/2 - width/2, bounds[1] + bounds[3]/2 - height/2, width, height]; baseWidth = width; cameraChanged();
}
function zoom(factor, anchor) {
  const next = camera[2] * factor; if (next < baseWidth/100 || next > baseWidth*100) return;
  const point = anchor || [camera[0]+camera[2]/2, camera[1]+camera[3]/2];
  camera = [point[0]-(point[0]-camera[0])*factor, point[1]-(point[1]-camera[1])*factor, next, camera[3]*factor]; cameraChanged();
}
function point(event) {return new DOMPoint(event.clientX, event.clientY).matrixTransform(canvas.getScreenCTM().inverse());}
canvas.addEventListener("wheel", event => {event.preventDefault(); const p = point(event); zoom(event.deltaY < 0 ? .85 : 1/.85, [p.x, p.y]);}, {passive:false});
let drag = null;
canvas.addEventListener("pointerdown", event => {if (event.target !== canvas || event.button !== 0) return; drag = {x:event.clientX,y:event.clientY,camera:[...camera],matrix:canvas.getScreenCTM().inverse()}; canvas.setPointerCapture(event.pointerId); canvas.classList.add("dragging");});
canvas.addEventListener("pointermove", event => {if (!drag) return; const a = new DOMPoint(drag.x, drag.y).matrixTransform(drag.matrix), b = new DOMPoint(event.clientX, event.clientY).matrixTransform(drag.matrix); camera = [drag.camera[0]-(b.x-a.x), drag.camera[1]-(b.y-a.y), ...drag.camera.slice(2)]; cameraChanged();});
for (const event of ["pointerup", "pointercancel", "lostpointercapture"]) canvas.addEventListener(event, () => {drag = null; canvas.classList.remove("dragging");});
$("zoom-in").onclick = () => zoom(.8); $("zoom-out").onclick = () => zoom(1.25); $("fit").onclick = fit;
async function edit(ticket) {
  if (!current || ticket !== revision) return;
  try {const data = await request("edit", {document:current.document,index:geometryIndex,length:$("length").value,thickness:$("thickness").value}); if (ticket === revision) install(data);}
  catch (error) {if (ticket === revision) {showError(error); status("Entrada no aceptada. Se mantiene el último dibujo válido.");}}
}
function pending() {dirty = true; $("export").disabled = true; $("geometry").disabled = true; $("discard").disabled = false;}
function scheduleEdit() {clearTimeout(timer); const ticket = ++revision; pending(); status("Cambios pendientes de validación…"); timer = setTimeout(() => edit(ticket), 350);}
$("length").addEventListener("input", scheduleEdit); $("thickness").addEventListener("input", scheduleEdit);
$("dimensions").onsubmit = event => {event.preventDefault(); clearTimeout(timer); pending(); edit(++revision);};
$("discard").onclick = () => {clearTimeout(timer); ++revision; install(current); status("Cambios descartados por solicitud. Se recuperaron los valores aceptados.");};
$("geometry").onchange = () => {clearTimeout(timer); ++revision; dirty = false; $("export").disabled = false; $("errors").hidden = true; geometryIndex = Number($("geometry").value); configIndex = 0; selection = null; updatePanel(); draw(); fit(); status("Geometría seleccionada. Se muestran sus valores aceptados.");};
$("configuration").onchange = () => {configIndex = Number($("configuration").value); selection = null; draw(); fit(); updateReinforcementNote();};
function openCreate() {$("create-error").textContent = ""; $("create-dialog").showModal();}
$("new").onclick = openCreate; $("empty-new").onclick = openCreate; $("cancel-create").onclick = () => $("create-dialog").close();
$("create-form").onsubmit = async event => {
  event.preventDefault(); clearTimeout(timer); const ticket = ++revision;
  try {const data = await request("create", Object.fromEntries(new FormData(event.target))); if (ticket !== revision) return; install(data, true); $("create-dialog").close();}
  catch (error) {$("create-error").textContent = errorText(error);}
};
$("file").onchange = async event => {
  const file = event.target.files[0]; event.target.value = ""; if (!file) return;
  if (current && !window.confirm("¿Reemplazar el proyecto abierto por el archivo seleccionado? Exporte antes los cambios que desee conservar.")) return;
  clearTimeout(timer); const ticket = ++revision;
  try {if (file.size > 2*1024*1024) throw {message:"El archivo supera 2 MiB."}; const data = await request("import", {document:await file.text()}); if (ticket === revision) install(data, true);}
  catch (error) {if (ticket === revision) showError(error);}
};
$("export").onclick = async () => {
  if (!current || dirty) return;
  try {const text = await request("export", {document:current.document}); const url = URL.createObjectURL(new Blob([text], {type:"application/json;charset=utf-8"})); const link = document.createElement("a"); link.href = url; link.download = "proyecto.json"; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); status("JSON canónico exportado.");} catch (error) {showError(error);}
};
window.addEventListener("beforeunload", event => {if (current) {event.preventDefault(); event.returnValue = "";}});
