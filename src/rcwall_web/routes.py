"""HTTP transport models are independent of the versioned domain contracts."""

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

from rcwall.io.json import dumps_project, loads_project
from rcwall_web.services import create_rectangle, edit_rectangle, present

router = APIRouter(prefix="/api")


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Dimensions(Input):
    length: StrictStr
    thickness: StrictStr


class Create(Dimensions):
    x: StrictStr
    y: StrictStr


class Document(Input):
    document: StrictStr


class Edit(Document, Dimensions):
    index: StrictInt


@router.post("/create")
def create(data: Create):
    return present(create_rectangle(data.length, data.thickness, data.x, data.y))


@router.post("/import")
def import_project(data: Document):
    return present(loads_project(data.document))


@router.post("/edit")
def edit(data: Edit):
    return present(edit_rectangle(data.document, data.index, data.length, data.thickness))


@router.post("/export")
def export(data: Document):
    return Response(
        dumps_project(loads_project(data.document)),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="proyecto.json"'},
    )
