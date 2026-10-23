"""Loopback-only, stateless FastAPI prototype. No project files or shared session store."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from rcwall.io.json import ProjectValidationError
from rcwall_web.routes import router
from rcwall_web.services import WebInputError

STATIC = Path(__file__).parent / "static"
MAX_BODY = 2 * 1024 * 1024


def problem(message, status=422, issues=None):
    return JSONResponse({"message": message, "issues": issues or []}, status_code=status)


def create_app():
    app = FastAPI(title="StructureLab · Muros", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        host = request.url.hostname
        origin = request.headers.get("origin")
        if host not in {"127.0.0.1", "localhost", "[::1]", "::1"}:
            return problem("Acceso permitido únicamente desde el servidor local.", 403)
        if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
            return problem("La solicitud debe proceder de esta misma aplicación.", 403)
        if request.method == "POST":
            if request.headers.get("content-type", "").split(";")[0] != "application/json":
                return problem("Envíe los datos como JSON.", 415)
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > MAX_BODY:
                    return problem("El proyecto supera el límite de transporte de 2 MiB.", 413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.exception_handler(ProjectValidationError)
    async def invalid_project(request, exc):
        messages = {
            "greater_than": "El valor debe ser mayor que cero.",
            "decimal_input": "Introduzca un decimal válido con punto decimal.",
            "missing": "Falta un campo obligatorio.",
            "missing_reference": "Existe una referencia a una entidad ausente.",
            "duplicate_id": "Hay identificadores repetidos.",
            "invalid_json": "El archivo no contiene JSON válido.",
            "duplicate_json_key": "El JSON contiene claves repetidas.",
        }
        return problem(
            "El proyecto no se ha modificado. Revise los datos.",
            issues=[
                {
                    "path": list(i.path),
                    "code": i.code,
                    "message": messages.get(i.code, "El dato no cumple el contrato canónico V0.1."),
                }
                for i in exc.report.issues
            ],
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return problem(
            "Solicitud inválida: las magnitudes deben enviarse como texto "
            "y todos los campos deben ser válidos."
        )

    @app.exception_handler(WebInputError)
    async def unsupported(request, exc):
        return problem(str(exc))

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    app.include_router(router)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


app = create_app()
