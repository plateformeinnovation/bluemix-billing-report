# Open Groupe Bluemix Billing Report

A [Flask](https://github.com/pallets/flask) web application for billing report of Open Groupe's Bluemix platform.

The application itself is run on Bluemix: [OPEN Bluemix Billing Report](https://open-bluemix-dashboard.eu-gb.mybluemix.net/)

This repository is using for Continious Integration, every update will trigger a new build and deploy cycle in Bluemix Platform.

## Run & test application locally

Run `run.py` with a specified `port` and an optional flag `dev`, ex:
```python
python run.py port [dev]
```
By default, the web application exposes on all the interfaces of the machine: `0.0.0.0:{port}`

The `dev` flag means that we provide Bluemix account authentication information locally in `bx_report/resource/ENV_VARIABLE`. In production environment, all authentication informations are provided by system environment varaibles.
