# based on image python 2.7
FROM python:2.7

ENV BXVERSION=0.4.5_amd64 BXREPORT_HOME=/opt/bluemix-report

RUN apt-get update && apt-get install -y apt-transport-https
RUN wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | apt-key add - &&\
    echo "deb http://packages.cloudfoundry.org/debian stable main" | tee /etc/apt/sources.list.d/cloudfoundry-cli.list
RUN wget http://public.dhe.ibm.com/cloud/bluemix/cli/bluemix-cli/Bluemix_CLI_$BXVERSION.tar.gz -O Bluemix_CLI.tar.gz && \
      tar -xvf Bluemix_CLI.tar.gz && \
      cd Bluemix_CLI && \
      ./install_bluemix_cli
RUN apt-get update && apt-get install -y cf-cli

# indicate the working directory for RUN, CMD, ENTRYPOINT
WORKDIR ${BXREPORT_HOME}
ADD . ${BXREPORT_HOME}
RUN pip install -r requirements.txt

# default docker execution command
CMD ["python","/opt/bluemix-report/run.py"]