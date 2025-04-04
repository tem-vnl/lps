# Lightweight Proctoring System (LPS)

## Description

LPS is a lightweight proctoring software intended to be be used in for digital examinations. This repository contains a proof of concept of the client side application. When running, the proctoring software will monitor the users gaze to prevent external devices from being used, combined with monitoring running software on the system used for taking the exam. Upon completing an exam, a report will be generated containging timestamped entries for when users gazed away for noticable periods of time, and for applications started and stopped, including browser tabs.

## Getting started

Run the folloing command to install all necessary python packages (requires python3 and pipx)
`cat requirements.txt | xargs pipx install --include-deps`

Run the following command to make sure that all apps are in your PATH
`pipx ensurepath`
