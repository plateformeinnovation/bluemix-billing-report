# Open Groupe Bluemix Billing Tool

A web application for [billing report of Open Groupe's bluemix services and applications](https://open-bluemix-dashboard.eu-gb.mybluemix.net/)
.

This repository is mainly used for continious integration(CI), each commit will kick off a new build and re-deploy it on bluemix.

## Run application
To run application locally, you need to install cloud foundry cf cli, bluemix cli, and also all the python dependencies library, then configure your PostgreSQL server properly to store collected billing information and start application by:
```python
python run.py {port} {flag}
```
`port`: the port on which the application runs, by default it exposes on all the interfaces: `0.0.0.0:{port}`

`flag`: 
* `dev`: providing bluemix account authentication information locally in `bx_report/resource/ENV_VARIABLE`. 
* `prod`: all authentication informations are provided by system environment varaibles.
