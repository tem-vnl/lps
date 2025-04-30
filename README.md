# Lightweight Proctoring System (LPS)

## Description

LPS is a lightweight proctoring software intended to be be used for digital examinations. This repository contains a proof of concept of the client side application. When running, the proctoring software will monitor the users gaze to prevent external devices from being used, combined with supplying a safe browser window for the user to complete the exam in. Tabs in this browser will be monitored and all other applications will be temporarily blocked from using the network. Upon completing an exam, a report will be generated containging timestamped entries for when users gazed away for noticable periods of time, and for url:s visited that are not whitelisted.

## Project plan

[Overleaf document *view-only](https://www.overleaf.com/read/tkbgctjyxbqk#17af24)

## Getting started

This project is dependency managed by poetry, to get started first install poetry:

```shell
pipx install poetry
```

Run the following command to install dependencies:

```shell
poetry install
```

You can then start the application by running:

```shell
poetry run python src
```

This repo uses TKinter, make sure that your python version is built with TKinter. This is not standard on many OS. For Linux, you can run the following command to get python with tkinter. Make sure this is also the version in use after installing.

```shell
sudo apt-get install python3-tk
```

Need to add any dependencies? Use poetry and do not install or edit dependencies manually.

If you are running into problems with VS Code python interpreter not picking up your poetry environment, please check the [help section](#vs-code-python-interpreter-with-poetry).

__Problems installing with poetry?__

Some of the packages takes a long time to install first time, and has some system dependencies such as cmake, dbus-1, etc, please check the [help section](#missing-global-dependencies).

## Testing

This project uses pytest for automated testing. To run the tests locally:

```bash
pytest
```

## Help

### Missing global dependencies?

If you are running into problems when runnint `poetry install` it is very likely that you are missing build-tools that the python dependencies rely on when being built and installed. Please carefully check the poetry output in yellow, it often lists missing packages on the last few lines, and install any build-dependencies manually.

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
