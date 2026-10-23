// All numbers here belong to the disposable view, never to the canonical definition.
export function createViewer(canvas, scene, zoomLabel, onSelect) {
  let camera = [-100, -300, 1200, 700];
  let baseWidth = 1200;
  let drag = null;

  function cameraChanged() {
    canvas.setAttribute("viewBox", camera.join(" "));
    zoomLabel.textContent = `${Math.round(baseWidth / camera[2] * 100)} %`;
  }

  function fit(bounds = [0, 0, 1000, 200]) {
    const width = Math.max(bounds[2] * 1.3, 1);
    const height = Math.max(bounds[3] * 1.8, width * 0.55);
    camera = [
      bounds[0] + bounds[2] / 2 - width / 2,
      bounds[1] + bounds[3] / 2 - height / 2,
      width, height,
    ];
    baseWidth = width;
    cameraChanged();
  }

  function zoom(factor, anchor) {
    const width = camera[2] * factor;
    if (width < baseWidth / 100 || width > baseWidth * 100) return;
    const point = anchor || [camera[0] + camera[2] / 2, camera[1] + camera[3] / 2];
    camera = [
      point[0] - (point[0] - camera[0]) * factor,
      point[1] - (point[1] - camera[1]) * factor,
      width, camera[3] * factor,
    ];
    cameraChanged();
  }

  function shape(tag, attributes, key, label, selection) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
    const kind = tag === "rect" ? "wall-shape" : "bar-shape";
    node.setAttribute("class", `${kind}${selection === key ? " selected" : ""}`);
    node.setAttribute("tabindex", "0");
    node.setAttribute("role", "button");
    node.setAttribute("aria-label", label);
    node.addEventListener("click", (event) => {
      event.stopPropagation();
      onSelect(key);
    });
    node.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onSelect(key);
        scene.querySelector(`[aria-label="${label}"]`)?.focus();
      }
    });
    scene.append(node);
  }

  function draw(graphics, selection) {
    scene.replaceChildren();
    if (!graphics?.rectangle) return;
    shape("rect", graphics.rectangle, "wall", "Seleccionar contorno del muro", selection);
    graphics.circles.forEach((circle, index) => {
      shape("circle", circle, index, `Seleccionar barra ${index + 1}`, selection);
    });
  }

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const point = new DOMPoint(event.clientX, event.clientY)
      .matrixTransform(canvas.getScreenCTM().inverse());
    zoom(event.deltaY < 0 ? 0.85 : 1 / 0.85, [point.x, point.y]);
  }, { passive: false });

  canvas.addEventListener("pointerdown", (event) => {
    if (event.target !== canvas || event.button !== 0) return;
    drag = {
      x: event.clientX, y: event.clientY,
      camera: [...camera], matrix: canvas.getScreenCTM().inverse(),
    };
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add("dragging");
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const start = new DOMPoint(drag.x, drag.y).matrixTransform(drag.matrix);
    const end = new DOMPoint(event.clientX, event.clientY).matrixTransform(drag.matrix);
    camera = [
      drag.camera[0] - (end.x - start.x),
      drag.camera[1] - (end.y - start.y),
      ...drag.camera.slice(2),
    ];
    cameraChanged();
  });
  for (const event of ["pointerup", "pointercancel", "lostpointercapture"]) {
    canvas.addEventListener(event, () => {
      drag = null;
      canvas.classList.remove("dragging");
    });
  }
  return { draw, fit, zoom };
}
