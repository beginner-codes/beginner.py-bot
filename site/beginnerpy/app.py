from os import environ
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


async def homepage(request):
    return JSONResponse(
        {
            "user": environ.get("POSTGRES_USER", None),
            "password": environ.get("POSTGRES_PASSWORD", None),
            "db": environ.get("POSTGRES_DB", None),
        }
    )


app = Starlette(debug=True, routes=[Route("/", homepage)])
