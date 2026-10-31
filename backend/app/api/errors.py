from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _body(status: int, code: str, message: str, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or {}}})


def install(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http(_: Request, e: HTTPException):
        return _body(e.status_code, str(e.status_code), str(e.detail))

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, e: RequestValidationError):
        return _body(422, "validation_error", "Invalid request", {"errors": jsonable(e.errors())})


def jsonable(errs):
    return [{"loc": list(x["loc"]), "msg": x["msg"]} for x in errs]
