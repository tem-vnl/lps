# Lightweight Proctoring System (LPS)

## Description

LPS is a lightweight proctoring software intended to be be used in for digital examinations. This repository contains a proof of concept of the client side application. When running, the proctoring software will monitor the users gaze to prevent external devices from being used, combined with monitoring running software on the system used for taking the exam. Upon completing an exam, a report will be generated containging timestamped entries for when users gazed away for noticable periods of time, and for applications started and stopped, including browser tabs.

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
