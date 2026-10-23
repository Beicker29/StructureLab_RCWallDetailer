"""The optional web adapter must not change the canonical model or share editor state."""

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from rcwall.io.json import dumps_project, loads_project, read_project
from rcwall_web.app import create_app

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/project_v0_1.json"


@pytest.fixture
def client():
    with TestClient(create_app(), base_url="http://127.0.0.1:8000") as connection:
        yield connection


def create(client, **changes):
    data = {"length": "3000.000000000000000000000000001", "thickness": "200.00", "x": "0", "y": "0"}
    return client.post("/api/create", json=data | changes)


def rich_document():
    data = read_project(EXAMPLE).model_dump(mode="json")
    data["bar_layouts"].append(
        {
            "layout_id": "EXPLICIT",
            "config_id": "C1",
            "distribution": {
                "pattern": "EXPLICIT",
                "bars": [
                    {
                        "bar_id": "B1",
                        "position": {"x_mm": "100.000000000000000000001", "y_mm": "50.00"},
                        "diameter_mm": "16.00",
                    },
                    {
                        "bar_id": "B2",
                        "position": {"x_mm": "2900", "y_mm": "150"},
                        "diameter_mm": "20",
                    },
                ],
            },
        }
    )
    data["bar_layouts"][0]["distribution"]["quantity"] = 9007199254740993
    return dumps_project(loads_project(json.dumps(data)))


def test_create_and_export_exact_canonical_json(client):
    response = create(client)
    assert response.status_code == 200
    payload = response.json()
    project = loads_project(payload["document"])
    assert str(project.geometries[0].shape.length_mm) == "3000.000000000000000000000000001"
    assert str(project.geometries[0].shape.thickness_mm) == "200.00"
    assert not project.sections and not project.walls and not project.bar_layouts
    assert project.project_id != project.geometries[0].geometry_id
    exported = client.post("/api/export", json={"document": payload["document"]})
    assert exported.text == payload["document"]
    assert "attachment" in exported.headers["content-disposition"]


@pytest.mark.parametrize(
    "value", ["0", "-1", "NaN", "Infinity", "1,5", "", " 200", 200, 1.2, True, None]
)
def test_invalid_dimensions_never_accepted(client, value):
    response = create(client, length=value)
    assert response.status_code == 422
    assert "message" in response.json()


def test_origin_is_required_and_preserved(client):
    assert client.post("/api/create", json={"length": "2", "thickness": "3"}).status_code == 422
    project = loads_project(create(client, x="-15.000", y="1e30").json()["document"])
    assert str(project.geometries[0].shape.origin.x_mm) == "-15.000"
    assert str(project.geometries[0].shape.origin.y_mm) == "1E+30"


def test_import_export_and_graphics_preserve_bars_and_large_integers(client):
    document = rich_document()
    response = client.post("/api/import", json={"document": document})
    assert response.status_code == 200
    payload = response.json()
    assert payload["document"] == document
    config = payload["geometries"][0]["configurations"][0]
    assert len(config["graphics"]["circles"]) == 2
    assert config["bars"][0]["x"] == "100.000000000000000000001"
    assert config["bars"][0]["diameter"] == "16.00"
    assert config["pending"] == 1
    assert client.post("/api/export", json={"document": payload["document"]}).text == document


def test_edit_changes_only_declared_dimensions(client):
    document = rich_document()
    response = client.post(
        "/api/edit",
        json={
            "document": document,
            "index": 0,
            "length": "3500.000000000000000001",
            "thickness": "250.00",
        },
    )
    assert response.status_code == 200
    expected = loads_project(document).model_dump(mode="json")
    expected["geometries"][0]["shape"].update(
        length_mm="3500.000000000000000001", thickness_mm="250.00"
    )
    assert json.loads(response.json()["document"]) == expected
    assert (
        client.post(
            "/api/edit", json={"document": document, "index": 0, "length": "0", "thickness": "250"}
        ).status_code
        == 422
    )
    assert client.post("/api/export", json={"document": document}).text == document


@pytest.mark.parametrize("index", [-1, 4, 0.1, True])
def test_edit_rejects_invalid_target(client, index):
    assert (
        client.post(
            "/api/edit",
            json={"document": rich_document(), "index": index, "length": "3", "thickness": "4"},
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "document",
    [
        '{"a":1,"a":2}',
        "not json",
        '{"schema_version":"2"}',
        '{"project_id":"P","schema_version":"0.1.0","units":"cm"}',
    ],
)
def test_import_and_export_reject_invalid_documents(client, document):
    for operation in ["import", "export"]:
        assert client.post(f"/api/{operation}", json={"document": document}).status_code == 422


def test_full_domain_validation_including_references(client):
    data = json.loads(rich_document())
    data["bar_layouts"][0]["config_id"] = "ABSENT"
    response = client.post("/api/import", json={"document": json.dumps(data)})
    assert response.status_code == 422
    assert any(i["code"] == "missing_reference" for i in response.json()["issues"])


def test_two_clients_have_no_shared_project_or_default_current_state(client):
    with TestClient(client.app, base_url="http://127.0.0.1:8000") as other:
        first = create(client, length="100").json()
        second = create(other, length="200").json()
        assert (
            loads_project(first["document"]).project_id
            != loads_project(second["document"]).project_id
        )
        changed = client.post(
            "/api/edit",
            json={"document": first["document"], "index": 0, "length": "150", "thickness": "50"},
        )
        assert changed.status_code == 200
        assert (
            other.post("/api/export", json={"document": second["document"]}).text
            == second["document"]
        )
        assert other.post("/api/export", json={}).status_code == 422
        assert not client.cookies and not other.cookies


def test_polygon_preserved_but_not_editable(client):
    data = json.loads(create(client).json()["document"])
    data["geometries"][0]["shape"] = {
        "kind": "POLYGON",
        "outer": [
            {"x_mm": "0", "y_mm": "0"},
            {"x_mm": "10", "y_mm": "0"},
            {"x_mm": "0", "y_mm": "10"},
        ],
    }
    document = dumps_project(loads_project(json.dumps(data)))
    imported = client.post("/api/import", json={"document": document}).json()
    assert imported["document"] == document
    assert not imported["geometries"][0]["rectangular"]
    assert (
        client.post(
            "/api/edit", json={"document": document, "index": 0, "length": "10", "thickness": "2"}
        ).status_code
        == 422
    )


def test_alternative_configurations_are_not_superimposed(client):
    data = json.loads(rich_document())
    data["configurations"].append({"config_id": "C2", "geometry_id": "G1"})
    views = client.post("/api/import", json={"document": json.dumps(data)}).json()["geometries"][0][
        "configurations"
    ]
    assert len(views) == 2
    assert len(views[0]["bars"]) == 2
    assert views[1]["bars"] == []


def test_large_origin_projection_does_not_cancel_small_dimensions(client):
    result = create(client, x="1e100", y="-1e100", length="3", thickness="1").json()
    graphics = result["geometries"][0]["configurations"][0]["graphics"]
    assert graphics["rectangle"]["width"] == 1000
    assert graphics["rectangle"]["height"] == pytest.approx(1000 / 3)
    tiny = create(client, length="1e-400", thickness="1e400").json()
    assert tiny["geometries"][0]["configurations"][0]["graphics"]["warning"]
    assert str(loads_project(tiny["document"]).geometries[0].shape.length_mm) == "1E-400"


def test_local_security_boundaries_and_size_limit(client):
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 403
    assert create(client).status_code == 200
    assert (
        client.post("/api/create", json={}, headers={"Origin": "https://evil.example"}).status_code
        == 403
    )
    assert (
        client.post("/api/create", content="{}", headers={"Content-Type": "text/plain"}).status_code
        == 415
    )
    assert client.post("/api/import", json={"document": "x" * (2 * 1024 * 1024)}).status_code == 413
    assert (
        client.post(
            "/api/create", content="{", headers={"Content-Type": "application/json"}
        ).status_code
        == 422
    )
    response = client.get("/")
    assert response.status_code == 200
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert '<html lang="es">' in response.text
    for name in ["style.css", "app.js"]:
        assert client.get(f"/static/{name}").status_code == 200


def test_graphic_resource_limit_preserves_canonical_project(client):
    response = create(client, length="1e1000000")
    assert response.status_code == 200
    payload = response.json()
    graphics = payload["geometries"][0]["configurations"][0]["graphics"]
    assert graphics["rectangle"] is None
    assert "Vista omitida" in graphics["warning"]
    assert str(loads_project(payload["document"]).geometries[0].shape.length_mm) == "1E+1000000"
    assert (
        client.post("/api/export", json={"document": payload["document"]}).text
        == payload["document"]
    )


def test_untrusted_labels_remain_data(client):
    data = json.loads(rich_document())
    label = '<img src=x onerror="alert(1)">'
    data["geometries"][0]["description"] = label
    response = client.post("/api/import", json={"document": json.dumps(data)})
    assert response.json()["geometries"][0]["label"] == label
    script = client.get("/static/app.js").text
    assert "innerHTML" not in script and "JSON.parse" not in script
