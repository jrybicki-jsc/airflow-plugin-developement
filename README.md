---
title: Airflow Plugin Development Tutorial
author: Jedrzej Rybicki
header-includes:
  - \usepackage{pmboxdraw}
---

A comprehensive guide to extending Apache Airflow 3.x with custom plugins for API and UI enhancements.

---

## Introduction

Airflow Plugins allow you to extend the capabilities and user interface of Apache Airflow. While many plugin examples exist online, most reference older Airflow versions. **Airflow v3** brought substantial changes:

- Major overhaul of internals
- Modern React-based user interface
- New plugin mechanisms

This tutorial covers:
1. Simple API extension
2. UI extension with React
3. Packaging the plugin for easy installation

### Prerequisites

- Basic Python programming knowledge
- Basic React programming knowledge
- Familiarity with tooling: git, uv, pnpm

---

## 1. Setup

### 1.1 Create Plugin Project with uv

We'll use `uv`'s project mode to create a proper, reproducible development environment. This ensures dependencies are tracked in `pyproject.toml` and locked in `uv.lock` for consistency.

```bash
# Create project structure
cd ~/airflow-dev
uv init airflow-plugin-dev
cd airflow-plugin-dev

# Add Airflow dependencies (tracked in pyproject.toml)
uv add "apache-airflow-core==3.2.0"
```

**What this does:**
- Creates `pyproject.toml` with dependency declarations
- Creates `uv.lock` with exact resolved versions
- Creates `.venv` virtual environment automatically
- `uv run` commands use this managed environment

### 1.2 Initialize Airflow Standalone

```bash
export AIRFLOW_HOME=~/airflow-dev/airflow
```
This will set the location of the airflow configuration file, the dags and the plugin folder.

```bash
# Run Airflow within the managed environment
uv run airflow standalone
```

The standalone mode runs an all-in-one Airflow instance accessible at `http://127.0.0.1:8080`. Upon first start the airflow will generate random password which will be printed on the screen. It can also be found in `~/airflow-dev/airflow/simple_auth_manager_passwords.json.generated`.


---

## 2. First Plugin: API Extension

This plugin extends the Airflow API with custom endpoints.

### 2.1 Create the Plugin Structure

```bash
# Create plugins directory inside your project
mkdir $AIRFLOW_HOME/plugins

# Create the plugin file
touch $AIRFLOW_HOME/plugins/first_plugin.py
```

### 2.2 Plugin Code

```python
# $AIRFLOW_HOME/plugins/first_plugin.py
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from airflow.plugins_manager import AirflowPlugin
from airflow.models import DagRun

app = FastAPI()


@app.get("/mydags")
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
```

This is a very simple plugin. It extends the Airflow API with two endpoints (`/hello` and `/mydags). The first one just returns a static text back. The second is added to show that plugins can access the internals of Airflow and do something more complicated. It will just iterate through the list of dag runs and return a list containg dag run details. The same information can be extracted from standard Airflow API but the goal here was just to exercise it. Furthermore the code contains some boilerplate to integrate the created endpoints into the Airflow server.



### 2.3 Start Airflow and Test

1. **Start Airflow standalone** (if not already running):
   ```bash
   cd ~/airflow-dev/airflow-plugin-dev
   uv run airflow standalone
   ```

2. **Navigate to the plugins page:**
   ```
   http://127.0.0.1:8080/admin/plugins
   ```
   You should see your plugin listed.

3. **Test the API endpoints:**

   First, get a bearer token via the browser:
   - Go to `http://127.0.0.1:8080/docs`
   - Click "Authorize" at the top
   - Enter a token value (e.g., `blah`)
   - Click "Authorize"

   Then test with curl:
   ```bash
   curl -X GET -H "Authorization: Bearer *** http://localhost:8080/first-plugin/hello
   curl -X GET -H "Authorization: Bearer *** http://localhost:8080/first-plugin/mydags
   ```

   Or use a web browser directly:
   ```
   http://localhost:8080/first-plugin/hello
   ```

It should answer with "Hello world!" (regardless of the method you have used to test it). You can also test the `/mydags` endpoint with browser in a similar fashion.

---

## 3. Second Plugin: UI Extension

This plugin extends the Airflow UI with a React-based interface.

### 3.1 Plugin Toolkit

Clone the Apache Airflow repository to access the plugin development tools:

```bash
git clone https://github.com/apache/airflow.git ~/airflow-dev/airflow-git
cd ~/airflow-dev/airflow-git
```

The plugin tools are located at: `airflow/dev/react-plugin-tools`

### 3.2 Create the Plugin Structure

```bash
# Create the plugin with bootstrap tool
cd ~/airflow-git/dev/react-plugin-tools/
uv run bootstrap.py second-plugin --dir $AIRFLOW_HOME/plugins/
```

This creates a scaffold with:
- React app structure
- Build configuration

### 3.3 Plugin Code (Python Backend)

```python
# $AIRFLOW_HOME/plugins/second_plugin.py
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
    return "Hello world! For the second time"



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
```

You should recognize some parts from the first plugin here. We extend the API again with a simple endpoint `/secondhello` which returns a simple string. Furthermore, the React web page is mounted as well (`/second-plugin/plugin-app/main.umd.cjs`). For now we don't modify the React code this will be done in the next section. You can modify the name of the plugin if you wish (`"name"`) or the location of the link that is added to Airflow. `nav` puts it on the left-hand side navigation panel.

### 3.4 Build the React Frontend

```bash
# Navigate to the plugin directory
cd $AIRFLOW_HOME/plugins/second-plugin

# Install dependencies
pnpm install

# Build the React app
pnpm build

# Remove deps (as it makes Airflow some problems)
rm -rf node_modules/
```

This generates the `dist/` directory with compiled static files. This step needs to be repeated each time React code is modified.

### 3.5 Test the UI Plugin

1. **Restart Airflow** to load the new plugin
2. **Navigate to your plugin:**
   ```
   http://127.0.0.1:8080/plugin/myplugin
   ```

A links should also appear on the left hand side in the main Airflow page. The web page allows to switch between dark and light mode of Airflow. Example is provided by the plugin tools.


### 3.6 Modifying React part of the plugin

Currently the plugin contains a page created by the plugin bootstrap tool. It allows for theme changes. One can modify the page by changing the file.

```React
# $AIRFLOW_HOME/plugins/second-plugin/src/pages/HomePage.tsx
import { Box, Button, Heading, Text, VStack } from "@chakra-ui/react";

import { useColorMode } from "src/context/colorMode";

export const HomePage = () => {
  const { colorMode, setColorMode } = useColorMode();

  return (
    <Box p={8} bg="bg.subtle" flexGrow={1} height="100%">
      <VStack gap={8} align="center" justify="center" flexGrow={1} height="100%">
        <Heading size="2xl" textAlign="center" color="fg">
          Welcome to Your New React App!
        </Heading>
        <Text>
        Hello plugin developer!
        </Text>
        <Text fontSize="lg" color="fg.muted">
          This project was bootstrapped with the Airflow React Plugin tool.
        </Text>
        <Button onClick={() => setColorMode(colorMode === "dark" ? "light" : "dark")} colorPalette="brand">
          Toggle Theme
        </Button>
      </VStack>
    </Box>
  );
};

```
The development of the UI in React is beyond the scope of this tutorial. We just add one paragraph with a custom text. The page can be tested independently from Airflow.


```bash
pnpm install
pnpm dev
```
This command will start a local server which is accessible under `http://localhost:5173/`. For the deployment on Airflow you have to redo the steps mentioned before:

```bash
# Navigate to the plugin directory
cd $AIRFLOW_HOME/plugins/second-plugin

# Install dependencies
pnpm install

# Build the React app
pnpm build

# Remove deps (as it makes Airflow some problems)
rm -rf node_modules/
```

After those steps and restarting Airflow, you should be able to view new version of the plugin web ui in Airflow.

### 3.7 Connecting the UI with the API in plugin

This is the final part of the plugin development. We modify the `HomePage.tsx` to fetch the information from the plugin endpoint `/secondhello` and presented its value to the user. This is by no means a proper or only way to do it, but it shows the principle that are required for complex plugin development.


```React
# $AIRFLOW_HOME/plugins/second-plugin/src/pages/HomePage.tsx
import { Box, Button, Heading, Text, VStack } from "@chakra-ui/react";
import React, { useState, useEffect } from "react";


export const HomePage = () => {
  const [greeting, setGreeting] = useState([]);
  const [loading, setLoading] = useState(true);

  console.log("Starting up");

  useEffect(() => {

    fetch("/second-plugin/secondhello")
      .then(response => response.json())
      .then(json => {
          console.log("Response fetched");
          console.log(json);

          setGreeting(json);
          setLoading(false);
      })
      .catch(error => console.error('Error fetching data:', error));

  }, []);


  if (loading) return (<>Loading...</>);

  return (
      <div><h1 class="LHeading">{greeting}</h1></div>
  );
};

```

Please remember to build the UI after the modifications, subsequently you can test the newly developed plugin in the Airflow. It should print the greetings returned from the endpoint of our plugin.


---

## 4. Packaging the Plugin

To make installation easier, package your plugin as a Python package using `uv`.

### 4.1 Project Structure

```
my-airflow-plugin/
├── pyproject.toml
├── uv.lock
├── src/
│   └── my_airflow_plugin/
│       ├── __init__.py
│       ├── plugin.py
│       └── frontend/
│           └── dist/
└── README.md
```

### 4.2 pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-airflow-plugin"
version = "0.1.0"
dependencies = [
    "apache-airflow>=3.0.0",
]

[project.entry-points."airflow.plugins"]
my_plugin = "my_airflow_plugin.plugin:MyAirflowPlugin"
```

### 4.3 Build and Install

```bash
# Build the package
uv build

# Install in editable mode for development
uv pip install -e .

# Or install as a regular package
uv pip install dist/my_airflow_plugin-0.1.0-py3-none-any.whl
```

Airflow will automatically discover and load the plugin via the entry point.

---

## 5. Troubleshooting

### Common Issues

1. **Plugin not showing in admin/plugins**
   - Check `AIRFLOW__CORE__PLUGINS_PATH` environment variable
   - Check airflow.cfg for plugins location
   - Ensure plugin file is in the correct directory
   - Restart Airflow after adding new plugins

2. **React app not loading**
   - Verify the `dist/` directory exists
   - Check that `pnpm build` completed successfully
   - Ensure the path in `StaticFiles` is correct
   - Some browsers use caching which does not update quick enough

3. **API endpoints returning 404**
   - Verify the router prefix matches your URL
   - Check that the plugin is loaded (check logs)
   - Ensure proper authentication/bearer token

4. **Dependencies not resolving**
   - Run `uv sync` to refresh the environment
   - Check `uv.lock` for version conflicts
   - Try `uv lock --reinstall` to force resolution

---

## 7. Next Steps

- Explore the [Airflow Plugin Documentation](https://airflow.apache.org/docs/)
- Study existing plugins in the Airflow repository
- Contribute your plugins back to the community

---

*Last updated: June 2026 | Airflow Version: 3.2.0*
