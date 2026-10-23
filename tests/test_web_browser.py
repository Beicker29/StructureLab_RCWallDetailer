"""Opt-in browser checks. Automated output never overwrites curated evidence."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

if os.environ.get("RCWALL_BROWSER_TESTS") != "1":
    pytest.skip(
        "Active RCWALL_BROWSER_TESTS=1 para las pruebas de navegador.", allow_module_level=True
    )

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Error as BrowserError
from playwright.sync_api import expect, sync_playwright

from rcwall.io.json import dumps_project, loads_project, read_project

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ui_output(tmp_path, request):
    configured = os.environ.get("RCWALL_UI_OUTPUT")
    base = Path(configured).resolve() if configured else tmp_path
    curated = (ROOT / "outputs/ui").resolve()
    if base == curated or curated in base.parents:
        pytest.fail("Las pruebas no deben sobrescribir las capturas seleccionadas en outputs/ui.")
    output = base / request.node.name
    output.mkdir(parents=True, exist_ok=True)
    return output


@pytest.fixture
def browser_page(server):
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960}, locale="es-CO")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(server)
        yield page
        browser.close()
        assert errors == []


def import_document(page, document=None):
    if document is None:
        document = (ROOT / "outputs/ui/ejemplo-barras.json").read_text(encoding="utf-8")
    page.locator("#file").set_input_files(
        {
            "name": "proyecto.json",
            "mimeType": "application/json",
            "buffer": document.encode("utf-8"),
        }
    )


def download_document(page):
    with page.expect_download() as download:
        page.get_by_role("button", name="Exportar JSON").click()
    return Path(download.value.path()).read_text(encoding="utf-8")


def fill_new_project(page, length="5000"):
    page.get_by_role("button", name="Nuevo muro").click()
    for name, value in [("length", length), ("thickness", "300"), ("x", "0"), ("y", "0")]:
        page.locator(f"#new-{name}").fill(value)


@pytest.mark.parametrize("cancel_action", ["button", "escape"])
def test_replacement_cancellation_keeps_project_draft_and_view(browser_page, cancel_action):
    page = browser_page
    import_document(page)
    expect(page.locator("circle.bar-shape")).to_have_count(2)
    original = download_document(page)
    page.get_by_role("button", name="Seleccionar barra 1", exact=True).click()
    page.get_by_role("button", name="Acercar", exact=True).click()
    camera = page.locator("#canvas").get_attribute("viewBox")
    inspector = page.locator("#properties").inner_text()
    page.locator("#length").fill("0")
    expect(page.locator("#errors")).to_be_visible()
    confirmations = []

    def cancel(dialog):
        confirmations.append(dialog.type)
        dialog.dismiss()

    page.on("dialog", cancel)
    fill_new_project(page)
    page.get_by_role("button", name="Crear geometría").click()
    assert confirmations == ["confirm"]
    expect(page.locator("#create-dialog")).to_be_visible()
    if cancel_action == "button":
        page.get_by_role("button", name="Cancelar", exact=True).click()
    else:
        page.keyboard.press("Escape")
    expect(page.locator("#length")).to_have_value("0")
    assert page.locator("#canvas").get_attribute("viewBox") == camera
    assert page.locator("#properties").inner_text() == inspector
    expect(page.locator("#export")).to_be_disabled()
    import_document(page, "{}")
    assert confirmations == ["confirm", "confirm"]
    expect(page.locator("#length")).to_have_value("0")
    page.get_by_role("button", name="Descartar cambios").click()
    assert download_document(page) == original


def test_failed_import_preserves_pending_values_and_exported_baseline(browser_page):
    page = browser_page
    import_document(page)
    expect(page.locator("#export")).to_be_enabled()
    original = download_document(page)
    page.locator("#thickness").fill("valor pendiente")
    expect(page.locator("#errors")).to_be_visible()
    page.on("dialog", lambda dialog: dialog.accept())
    import_document(page, '{"project_id":')
    expect(page.locator("#errors")).to_contain_text("JSON válido")
    expect(page.locator("#thickness")).to_have_value("valor pendiente")
    expect(page.locator("circle.bar-shape")).to_have_count(2)
    expect(page.locator("#save-state")).to_have_text("Cambios sin exportar")
    page.get_by_role("button", name="Descartar cambios").click()
    assert download_document(page) == original
    expect(page.locator("#save-state")).not_to_have_text("Cambios sin exportar")


def test_confirmed_replacements_and_late_edit_do_not_mix_projects(browser_page):
    page = browser_page
    import_document(page)
    expect(page.locator("#export")).to_be_enabled()
    pending = []
    page.route("**/api/edit", lambda route: pending.append(route))
    page.locator("#length").fill("3900.1234567890123456789")
    with page.expect_request("**/api/edit"):
        page.get_by_role("button", name="Validar cambios").click()
    page.on("dialog", lambda dialog: dialog.accept())
    fill_new_project(page, "5100.000000000000000001")
    page.get_by_role("button", name="Crear geometría").click()
    expect(page.locator("#create-dialog")).not_to_be_visible()
    expect(page.locator("#length")).to_have_value("5100.000000000000000001")
    for route in pending:
        with page.expect_response("**/api/edit"):
            route.fulfill(response=route.fetch())
    # Export goes through the accepted state after the old response has arrived.
    document = download_document(page)
    assert str(loads_project(document).geometries[0].shape.length_mm) == "5100.000000000000000001"
    assert loads_project(document).bar_layouts == ()
    import_document(page)
    expect(page.locator("circle.bar-shape")).to_have_count(2)
    expect(page.locator("#length")).to_have_value("3000.000000000000000000000000001")


def test_cancel_creation_in_flight_keeps_original_project(browser_page):
    page = browser_page
    import_document(page)
    expect(page.locator("#export")).to_be_enabled()
    original = download_document(page)
    pending = []
    page.route("**/api/create", lambda route: pending.append(route))
    page.on("dialog", lambda dialog: dialog.accept())
    fill_new_project(page)
    with page.expect_request("**/api/create"):
        page.get_by_role("button", name="Crear geometría").click()
    page.get_by_role("button", name="Cancelar", exact=True).click()
    for route in pending:
        with page.expect_response("**/api/create"):
            route.fulfill(response=route.fetch())
    assert download_document(page) == original
    expect(page.locator("circle.bar-shape")).to_have_count(2)


def test_geometric_warning_is_visible_and_bars_are_unchanged(browser_page, ui_output):
    page = browser_page
    import_document(page)
    warning = page.locator("#geometry-warning")
    expect(warning).to_be_visible()
    for message in [
        "coordenadas originales",
        "no redistribuye",
        "contención",
        "recubrimientos",
        "factibilidad constructiva",
        "no significa aprobación",
    ]:
        expect(warning).to_contain_text(message)
    original = json.loads(download_document(page))
    page.locator("#length").fill("50.000000000000001")
    expect(page.locator("#export")).to_be_enabled()
    page.get_by_role("button", name="Seleccionar barra 1", exact=True).click()
    expect(page.locator("#properties")).to_contain_text("100.000000000000000000001")
    changed = json.loads(download_document(page))
    original["geometries"][0]["shape"]["length_mm"] = "50.000000000000001"
    assert changed == original
    page.screenshot(path=str(ui_output / "advertencia-geometrica.png"), full_page=True)
    page.on("dialog", lambda dialog: dialog.accept())
    fill_new_project(page)
    page.get_by_role("button", name="Crear geometría").click()
    expect(page.locator("#create-dialog")).not_to_be_visible()
    expect(warning).not_to_be_visible()


def test_reload_guard_tracks_downloads_edits_and_discard(browser_page):
    page = browser_page
    fill_new_project(page)
    page.get_by_role("button", name="Crear geometría").click()
    expect(page.locator("#create-dialog")).not_to_be_visible()
    dialogs = []

    def stay(dialog):
        dialogs.append(dialog.type)
        dialog.dismiss()

    page.on("dialog", stay)
    with pytest.raises(BrowserError):
        page.reload(timeout=3000)
    assert dialogs == ["beforeunload"]
    expect(page.locator("#length")).to_have_value("5000")
    document = download_document(page)
    expect(page.locator("#save-state")).not_to_have_text("Cambios sin exportar")
    page.locator("#length").fill("0")
    expect(page.locator("#errors")).to_be_visible()
    with pytest.raises(BrowserError):
        page.reload(timeout=3000)
    assert dialogs == ["beforeunload", "beforeunload"]
    page.get_by_role("button", name="Descartar cambios").click()
    page.reload()
    expect(page.locator("#empty")).to_be_visible()
    assert dialogs == ["beforeunload", "beforeunload"]
    import_document(page, document)
    expect(page.locator("#export")).to_be_enabled()
    page.locator("#length").click()
    page.reload()
    assert dialogs == ["beforeunload", "beforeunload"]


def test_failed_or_old_export_does_not_mark_latest_version_saved(browser_page):
    page = browser_page
    fill_new_project(page)
    page.get_by_role("button", name="Crear geometría").click()
    expect(page.locator("#export")).to_be_enabled()
    page.route(
        "**/api/export",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"message":"Prueba de fallo"}',
        ),
    )
    page.get_by_role("button", name="Exportar JSON").click()
    expect(page.locator("#errors")).to_contain_text("Prueba de fallo")
    expect(page.locator("#save-state")).to_have_text("Cambios sin exportar")
    page.unroute("**/api/export")
    pending = []
    page.route("**/api/export", lambda route: pending.append(route))
    with page.expect_request("**/api/export"):
        page.get_by_role("button", name="Exportar JSON").click()
    page.locator("#length").fill("6000.000000000000001")
    expect(page.locator("#export")).to_be_enabled()
    with page.expect_download() as download:
        pending[0].fulfill(response=pending[0].fetch())
    downloaded = Path(download.value.path()).read_text(encoding="utf-8")
    assert str(loads_project(downloaded).geometries[0].shape.length_mm) == "5000"
    expect(page.locator("#length")).to_have_value("6000.000000000000001")
    expect(page.locator("#save-state")).to_have_text("Cambios sin exportar")
    page.unroute("**/api/export")
    download_document(page)
    expect(page.locator("#save-state")).not_to_have_text("Cambios sin exportar")


@pytest.fixture(scope="module")
def server():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "rcwall_web.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                with urlopen(url, timeout=1):
                    break
            except URLError:
                time.sleep(0.1)
        else:
            pytest.fail("El servidor local no arrancó.")
        yield url
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_browser_creation_editing_selection_zoom_pan_and_sessions(server, ui_output):
    output = ui_output
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 960}, locale="es-CO")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(server)
        page.get_by_role("button", name="Crear muro rectangular").click()
        for field, value in [
            ("new-length", "3000.000000000000000000001"),
            ("new-thickness", "240.00"),
            ("new-x", "-10.00"),
            ("new-y", "25"),
        ]:
            page.locator(f"#{field}").fill(value)
        page.get_by_role("button", name="Crear geometría").click()
        expect(page.locator("#create-dialog")).not_to_be_visible()
        expect(page.locator("rect.wall-shape")).to_have_count(1)
        page.get_by_role("button", name="Seleccionar contorno del muro").click()
        expect(page.locator("#properties")).to_contain_text("3000.000000000000000000001")
        expect(page.locator("rect.wall-shape")).to_have_class("wall-shape selected")
        page.screenshot(path=str(output / "01-contorno.png"), full_page=True)
        initial_height = page.locator("rect.wall-shape").get_attribute("height")
        page.locator("#thickness").fill("400.000000000000000000001")
        expect(page.locator("#export")).to_be_enabled()
        assert page.locator("rect.wall-shape").get_attribute("height") != initial_height
        accepted_width = page.locator("rect.wall-shape").get_attribute("width")
        page.locator("#length").fill("0")
        expect(page.locator("#errors")).to_be_visible()
        expect(page.locator("#export")).to_be_disabled()
        assert page.locator("rect.wall-shape").get_attribute("width") == accepted_width
        page.screenshot(path=str(output / "02-validacion.png"), full_page=True)
        page.get_by_role("button", name="Descartar cambios").click()
        expect(page.locator("#length")).to_have_value("3000.000000000000000000001")
        page.locator("#length").fill("3200")
        page.locator("#length").fill("3400.000000000000001")
        expect(page.locator("#export")).to_be_enabled()
        expect(page.locator("#properties")).to_contain_text("3400.000000000000001")
        with page.expect_download() as download:
            page.get_by_role("button", name="Exportar JSON").click()
        document = Path(download.value.path()).read_text(encoding="utf-8")
        assert str(loads_project(document).geometries[0].shape.length_mm) == "3400.000000000000001"
        before = page.locator("#canvas").get_attribute("viewBox")
        page.get_by_role("button", name="Acercar", exact=True).click()
        assert page.locator("#canvas").get_attribute("viewBox") != before
        box = page.locator("#canvas").bounding_box()
        page.mouse.move(box["x"] + 80, box["y"] + 70)
        before = page.locator("#canvas").get_attribute("viewBox")
        page.mouse.wheel(0, -200)
        expect(page.locator("#canvas")).not_to_have_attribute("viewBox", before)
        before = page.locator("#canvas").get_attribute("viewBox")
        page.mouse.down()
        page.mouse.move(box["x"] + 170, box["y"] + 130, steps=8)
        page.mouse.up()
        assert page.locator("#canvas").get_attribute("viewBox") != before
        page.screenshot(path=str(output / "03-zoom-desplazamiento.png"), full_page=True)
        with page.expect_download() as download:
            page.get_by_role("button", name="Exportar JSON").click()
        assert Path(download.value.path()).read_text(encoding="utf-8") == document
        for second in [context.new_page(), browser.new_context().new_page()]:
            second.goto(server)
            expect(second.locator("#empty")).to_be_visible()
            expect(second.locator("#export")).to_be_disabled()
            expect(second.locator("rect.wall-shape")).to_have_count(0)
        assert errors == []
        browser.close()


def test_browser_import_bars_untrusted_text_and_exact_export(server, ui_output):
    output = ui_output
    data = read_project(ROOT / "examples/project_v0_1.json").model_dump(mode="json")
    data["geometries"][0]["description"] = "Muro de prueba · barras declaradas"
    data["bar_layouts"][0]["distribution"]["quantity"] = 9007199254740993
    data["bar_layouts"].append(
        {
            "layout_id": "EXPLICIT",
            "config_id": "C1",
            "distribution": {
                "pattern": "EXPLICIT",
                "bars": [
                    {
                        "bar_id": "B1",
                        "position": {"x_mm": "100.000000000000000000001", "y_mm": "100"},
                        "diameter_mm": "32.00",
                    },
                    {
                        "bar_id": "B2",
                        "position": {"x_mm": "2900", "y_mm": "100"},
                        "diameter_mm": "32.00",
                    },
                ],
            },
        }
    )
    document = dumps_project(loads_project(json.dumps(data)))
    (output / "ejemplo-barras.json").write_text(document, encoding="utf-8")
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960}, locale="es-CO")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(server)
        page.locator("#file").set_input_files(
            {
                "name": "barras.json",
                "mimeType": "application/json",
                "buffer": document.encode("utf-8"),
            }
        )
        expect(page.locator("circle.bar-shape")).to_have_count(2)
        page.get_by_role("button", name="Seleccionar barra 1", exact=True).click()
        expect(page.locator("#properties")).to_contain_text("100.000000000000000000001")
        expect(page.locator("#properties")).to_contain_text("32.00")
        page.screenshot(path=str(output / "04-barra-explicita.png"), full_page=True)
        with page.expect_download() as download:
            page.get_by_role("button", name="Exportar JSON").click()
        assert Path(download.value.path()).read_text(encoding="utf-8") == document
        data["geometries"][0]["description"] = '<img src=x onerror="alert(1)">'
        page.on("dialog", lambda dialog: dialog.accept())
        page.locator("#file").set_input_files(
            {
                "name": "texto.json",
                "mimeType": "application/json",
                "buffer": json.dumps(data).encode("utf-8"),
            }
        )
        expect(page.locator("#geometry option")).to_have_text('<img src=x onerror="alert(1)">')
        expect(page.locator("img")).to_have_count(0)
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=str(output / "05-vista-estrecha.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert errors == []
        browser.close()
