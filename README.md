# Lightweight Proctoring System (LPS)

## Description

LPS is a lightweight proctoring software intended to be be used in for digital examinations. This repository contains a proof of concept of the client side application. When running, the proctoring software will monitor the users gaze to prevent external devices from being used, combined with monitoring running software on the system used for taking the exam. Upon completing an exam, a report will be generated containging timestamped entries for when users gazed away for noticable periods of time, and for applications started and stopped, including browser tabs.

## Project plan

[Overleaf document *view-only](https://www.overleaf.com/read/tkbgctjyxbqk#17af24)

## Getting started

This project is dependency managed by poetry, to get started first install poetry:

```shell
pipx install poetry
```

Run the following command to install dependencies:
__NOTE:__ dlib can take a long time to install, and requires cmake to be installed on your system.

```shell
poetry install
```

You can then start the application by running:

```shell
poetry run python src
```

Need to add any dependencies? Use poetry and do not install or edit dependencies manually.

If you are running into problems with VS Code python interpreter not picking up your poetry environment, please check the [help section](#vs-code-python-interpreter-with-poetry).

## Help

### VS Code python interpreter with poetry

If you are running into issues with VS Code not picking up on the correct environment, this is a fix that should work on any system.
This will configure poetry to save the .venv folder in the project directory:

```shell
poetry config virtualenvs.in-project true
```

Run the install command from the getting started guide, and after reloading VS Code, you should be able to pick the project .venv folder with the Python: Select interpreter from the command palette.

If you have allready created a virtual environment before changing your config settings, remove the current one using the following commands:

```shell
poetry env list  # shows the name of the current environment
poetry env remove <current environment>
poetry install  # will create a new environment using your updated configuration
```

[Source for quickfix](https://stackoverflow.com/questions/59882884/vscode-doesnt-show-poetry-virtualenvs-in-select-interpreter-option)
