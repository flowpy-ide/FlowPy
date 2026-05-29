![FlowPy Logo](docs/icon-svg.svg)

# FlowPy

A desktop IDE for modeling and executing algorithm flows with drag-and-drop nodes.

[![Release](https://img.shields.io/github/v/release/<ORG>/<REPO>?style=flat-square)](https://github.com/<ORG>/<REPO>/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/<ORG>/<REPO>/latest/total?style=flat-square)](https://github.com/<ORG>/<REPO>/releases/latest)
[![License](https://img.shields.io/badge/license-UNKNOWN-lightgrey?style=flat-square)](#license)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)]()
[![Windows](https://img.shields.io/badge/platform-Windows-brightgreen?style=flat-square)]()
[![Issues](https://img.shields.io/github/issues/<ORG>/<REPO>?style=flat-square)](https://github.com/<ORG>/<REPO>/issues)
[![Last commit](https://img.shields.io/github/last-commit/<ORG>/<REPO>?style=flat-square)](https://github.com/<ORG>/<REPO>)

---

## About

FlowPy is a desktop application for visually modeling and running algorithm flows using Python-style nodes. Users build flow graphs by dragging nodes onto the canvas, execute the flow, inspect live variable state, and generate source code from the graph.

## Key Features

- **Drag-and-drop flow editor**: Build workflows by placing nodes from the palette onto the canvas.
- **Run / Step / Stop**: Execute the flow at full speed or step through each node.
- **Live variable tracking**: See runtime variable values and sparkline charts.
- **Flow validation**: Prevent invalid flows from running.
- **Code generation**: Export generated code for Python, Java, C, C++, JavaScript and Pseudocode.
- **Rich node library**: Includes loops, decision blocks, I/O, file operations, functions, exception handling, lists, and more.
- **Undo / Redo**: Revert and replay edit steps.
- **Minimap, rulers and zoom**: Manage large flows with navigation helpers.
- **Sample flows**: Start quickly with built-in examples like `created_flows/tam_demo.flowpy`.
- **Style customization**: Adjust node colors and appearance.

## Why FlowPy?

FlowPy is designed for anyone who wants to visualize algorithm structure and build logic without writing code first. It is especially useful for:

- **Students**: Learning algorithm flow by visual example.
- **Educators**: Demonstrating flow diagrams in a tangible way.
- **Developers**: Quickly prototyping logic and generating code.
- **Non-technical users**: Modeling and testing processes without manual programming.

## Download & Installation

### Install from GitHub Releases

1. Open `https://github.com/<ORG>/<REPO>/releases/latest`.
2. Download the latest build: `FlowPy.exe` or `FlowPy-win64.zip`.
3. If you downloaded a ZIP archive, extract it.
4. Run `FlowPy.exe`.
5. If Windows SmartScreen appears, choose "More info" and then "Run anyway."

> Note: If an `.exe` package is available, Python installation may not be required.

### Run from source

1. Navigate to the project folder.
2. Create and activate a virtual environment.
3. Install dependencies.

```powershell
cd c:\yedekler\Flow-py\FlowPy
python -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## First Run Guide

1. Launch the application.
2. Choose "Start with sample flow" or "Start with empty canvas".
3. Drag nodes from the left panel onto the canvas.
4. Double-click a node to edit its properties.
5. Connect nodes to define execution flow.
6. Use the "Run" button to execute or "Step" to step through.
7. Watch console output and variable updates.
8. Save your work as a `.flowpy` file from the File menu.

## Screenshots

> **TODO:** Add actual UI screenshots under `docs/screenshots/`.

![FlowPy Main Screen](docs/screenshots/hero.png)
![Flow Designer](docs/screenshots/flow-builder.png)
![Code Generation](docs/screenshots/code-generator.png)

## System Requirements

- Windows 10 or Windows 11 (64-bit)
- 4 GB RAM recommended
- 200 MB free disk space
- Python 3.10+ and PyQt6 for source execution

## Project Structure

| Folder / File | Description |
| --- | --- |
| `main.py` | Main application entrypoint |
| `requirements.txt` | Python dependencies |
| `core/` | Interpreter, code generator, validation, settings, undo/redo |
| `models/` | Node and edge data models |
| `views/` | Qt UI components |
| `created_flows/` | Example `.flowpy` flows |
| `docs/` | Documentation and design assets |

## FAQ

### What if Windows SmartScreen blocks the app?
If the downloaded `.exe` is new or unsigned, SmartScreen may show a warning. Click "More info" and then "Run anyway."

### Where are projects stored?
FlowPy saves `.flowpy` files to the folder you choose during save. Sample flows live in `created_flows/`.

### How do I get generated code?
Use the code generation panel inside the app and copy the output for your chosen language.

### How do I update?
Download the newest release from GitHub Releases and replace the app files. Existing `.flowpy` projects remain unaffected.

### How do I report bugs?
Open a new issue in the project repository.

## Troubleshooting

- **Application will not start:** Ensure Python 3.10+ and PyQt6 are installed if running from source.
- **Missing dependency errors:** Run `python -m pip install -r requirements.txt`.
- **Save errors:** Run the app from a folder with write permission.
- **Flow not loading:** The `.flowpy` file may be corrupted; try a sample from `created_flows/`.
- **SmartScreen blocking:** Right-click the downloaded `.exe`, select "Properties," and unblock if necessary.

## Contributing

1. Fork the repository.
2. Create a new branch: `feature/<short-description>`.
3. Commit your changes.
4. Submit a pull request.

Please follow the existing `core/`, `models/`, and `views/` architecture.

## Roadmap

- Automated GitHub Releases packaging for Windows
- macOS / Linux support
- Improved `.flowpy` versioning and import/export
- Plugin support and node templates

## Technologies

- Python 3.10+
- PyQt6
- Qt-based desktop user interface
- Visual flow canvas, undo/redo, live variable tracking
- Code generation for Python, Java, C, C++, JavaScript, Pseudocode

## License

This repository does not yet contain a `LICENSE` file. Add an appropriate open source license before official distribution.

## Support

- Issues & feature requests: `https://github.com/<ORG>/<REPO>/issues`
- Maintainers: Erkan TURGUT, Aslı AYDIN
- Release notes: GitHub Releases
