from application import notification
import json 

from fastapi import FastAPI, Request, status
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware

from .config import settings
from .utils.gearman import JSONGearmanClient, JSONGearmanWorker

gm_client: JSONGearmanClient = JSONGearmanClient(settings.GEARMAN_CLIENT_HOST_LIST)
gm_worker: JSONGearmanWorker = JSONGearmanWorker(settings.GEARMAN_WORKER_HOST_LIST)


origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:3000"
]

def create_app():
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

    # middlewares 
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RawContextMiddleware, plugins = (plugins.RequestIdPlugin(), plugins.CorrelationIdPlugin()))

     # import routes.
    from .base import routes as baseRoutes 
    from .project import routes as projectRoutes
    from .session import routes as sessionRoutes
    from .institution import routes as institutionRoutes
    from .permission import routes as permissionRoutes
    from .notification import routes as notificationRoutes 
    from .base.analytics import routes as analyticsRoutes 
    app.include_router(baseRoutes.media_router)
    app.include_router(sessionRoutes.router)
    app.include_router(sessionRoutes.user_router)
    app.include_router(permissionRoutes.router)
    app.include_router(institutionRoutes.router)
    app.include_router(projectRoutes.router)
    app.include_router(notificationRoutes.router)
    app.include_router(analyticsRoutes.router)


    # override validation error
    @app.exception_handler(RequestValidationError)
    async def http_exception_handler(request, error):
        errors = []
        for err in json.loads(error.json()):
            errors.append({err['loc'][0]: err['msg']})
        return JSONResponse(content={'success': False, "error": errors}, status_code=status.HTTP_400_BAD_REQUEST)

    from .base.api_response import CustomException
    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.status,
            content={"success": False, "error": exc.error}
        )

    return app 


# import job files.
from .project.dataset.jobs import *
from .session.jobs import *
from .notification.jobs import *

