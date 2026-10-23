"""Opt-in end-to-end UI verification; screenshots are generated under outputs/ui."""

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
from playwright.sync_api import expect, sync_playwright

from rcwall.io.json import dumps_project, loads_project, read_project

ROOT = Path(__file__).resolve().parents[1]


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


def test_browser_creation_editing_selection_zoom_pan_and_sessions(server):
    output = ROOT / "outputs/ui"
    output.mkdir(parents=True, exist_ok=True)
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
        second = browser.new_context().new_page()
        second.goto(server)
        expect(second.locator("#empty")).to_be_visible()
        expect(second.locator("#export")).to_be_disabled()
        expect(second.locator("rect.wall-shape")).to_have_count(0)
        assert errors == []
        browser.close()


def test_browser_import_bars_untrusted_text_and_exact_export(server):
    output = ROOT / "outputs/ui"
    output.mkdir(parents=True, exist_ok=True)
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
