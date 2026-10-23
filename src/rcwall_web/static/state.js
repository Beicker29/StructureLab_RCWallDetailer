// One module instance per page. No shared storage and no parsing of canonical JSON.
export const state = {
  current: null,
  geometryIndex: 0,
  configIndex: 0,
  selection: null,
  pending: false,
  busy: false,
  revision: 0,
  generation: 0,
  savedDocument: null,
  timer: null,
};

export function selectedGeometry() {
  return state.current?.geometries[state.geometryIndex];
}

export function selectedConfig() {
  return selectedGeometry()?.configurations[state.configIndex];
}

export function invalidateRequests() {
  clearTimeout(state.timer);
  state.timer = null;
  return ++state.revision;
}

export function isCurrent(ticket) {
  return ticket === state.revision;
}

export function scheduleEdit(callback) {
  const ticket = invalidateRequests();
  state.pending = true;
  state.timer = setTimeout(() => callback(ticket), 350);
}

export function acceptProject(data, source = "edit") {
  state.current = data;
  state.pending = false;
  if (source !== "edit") {
    state.generation += 1;
    state.geometryIndex = Math.max(0, data.geometries.findIndex((g) => g.rectangular));
    state.configIndex = 0;
    state.selection = null;
    // An imported definition is recoverable from the user's source file.
    state.savedDocument = source === "import" ? data.document : null;
  }
}

export function markDownloaded(document, generation) {
  if (generation === state.generation) state.savedDocument = document;
}

export function hasUnsavedChanges() {
  return state.pending || Boolean(
    state.current && state.current.document !== state.savedDocument,
  );
}
