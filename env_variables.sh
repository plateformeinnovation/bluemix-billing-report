#!/bin/bash

# postgresql connection info provided by bluemix
export VCAP_SERVICES_COMPOSE_FOR_POSTGRESQL_0_CREDENTIALS_URI='postgres://login:password@host:port/database'

# bluemix login and password
export BX_LOGIN=''
export BX_PASSWORD=''

# time interval for loading database
export BX_SLEEP=43200
