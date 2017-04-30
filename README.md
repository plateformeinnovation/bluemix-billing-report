# Open Groupe Bluemix Billing Tool

A web application for [billing report of Open Groupe's bluemix services and applications](https://open-bluemix-dashboard.eu-gb.mybluemix.net/)
.

This repository is mainly using for continious integration(CI), every commit will kick off a new build task and re-deploy it on bluemix.

## Run application
```python
python run.py {port} {flag}
```
`port`: the port on which the application runs, by default it exposes on all the interfaces: `0.0.0.0:{port}`

`flag`: 
* `dev`: providing bluemix account authentication information locally in `bx_report/resource/ENV_VARIABLE`. 
* `prod`: all authentication informations are provided by system environment varaibles.
