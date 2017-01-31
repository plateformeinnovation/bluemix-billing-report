# Open Groupe Bluemix Billing Report

This is a web application developed on [Flask](https://github.com/pallets/flask) for Billing reporting of Bluemix platform for Open Groupe.

This repository is using for Continious Integration, every update will trigger a new build and deploy cycle in Bluemix Platform.

## Run & test application locally

Run `run.py` with a specified port and an optional flag `dev`, ex:
```python
python run.py port [dev]
```
By default, the web application exposes all interfaces (`0.0.0.0`) of the machine, so access it by `0.0.0.0:{port}`

The `dev` flag means that we provide Bluemix account authentication information locally in `src/resource/ENV_VARIABLE`. In production environment, it is provided by system environment varaibles.
