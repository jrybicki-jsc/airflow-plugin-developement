from pathlib import Path
from fastapi import FastAPI 
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.staticfiles import StaticFiles
import mimetypes

from airflow.plugins_manager import AirflowPlugin

mimetypes.add_type("application/javascript", ".cjs")

app = FastAPI()

react_app_directory = Path(__file__).parent.joinpath("second-plugin", "dist")
app.mount(
    "/plugin-app",
    StaticFiles(directory=react_app_directory, html=True),
    name="second-static",
)
    
@app.get("/secondhello")
def greet():
    return "Hello world!"


    
# Creating a FastAPI middleware that will operates on all the server api requests.
middleware_with_metadata = {
    "middleware": TrustedHostMiddleware,
    "args": [],
    "kwargs": {"allowed_hosts": ["*"]},
    "name": "My API Middleware",
}


class ResultsPlugin(AirflowPlugin):
    name = "second_plugin"

    def __init__(self) -> None:
        super().__init__()
    # Serve static files
    fastapi_apps = [
        {
            "app": app,
            "url_prefix": "/second-plugin",
            "name": "My Plugin Static Server",
        }
    ]

    # Register React application
    react_apps = [
        {
            "name": "My Plugin",
            "url_route": "myplugin",
            "bundle_url": "/second-plugin/plugin-app/main.umd.cjs",
            #Supported locations are Literal["nav", "dag", "dag_run", "task", "task_instance"],
            "destination": "nav"
        }
    ]

    fastapi_root_middlewares = [middleware_with_metadata]

