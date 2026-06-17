from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from airflow.plugins_manager import AirflowPlugin
from airflow.models import DagRun

app = FastAPI()


@app.get("/dags")
def dags():
    dag_runs = DagRun.find()
    dag_list = [{
            'run_id': run.run_id,
            'user': run.triggering_user_name, 
            'dag_id': run.dag_id,
            'start': run.start_date,
            'end': run.end_date,
            'duration': run.duration,
        } for run in dag_runs]
    
    return dag_list

@app.get("/hello")
def greet():
    return "Hello world!"


# Creating a FastAPI middleware that will operates on all the server api requests.
middleware_with_metadata = {
    "middleware": TrustedHostMiddleware,
    "args": [],
    "kwargs": {"allowed_hosts": ["*"]},
    "name": "First API",
}


class MyPlugin(AirflowPlugin):
    name = "First Plugin"
    fastapi_apps = [
        {
            "app": app,
            "url_prefix": "/first-plugin",
            "name": "First Pluging Server",
        }
    ]


    fastapi_root_middlewares = [middleware_with_metadata]
