# based on image python 2.7
FROM python:2.7

ENV BXVERSION=0.4.5_amd64
RUN apt-get update && apt-get install -y apt-transport-https &&  apt-get install -y wget
RUN wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | apt-key add - &&\
    echo "deb http://packages.cloudfoundry.org/debian stable main" | tee /etc/apt/sources.list.d/cloudfoundry-cli.list
RUN apt-get update && apt-get install -y cf-cli
RUN wget http://public.dhe.ibm.com/cloud/bluemix/cli/bluemix-cli/Bluemix_CLI_$BXVERSION.tar.gz -O Bluemix_CLI.tar.gz && \
      tar -xvf Bluemix_CLI.tar.gz && \
      cd Bluemix_CLI && \
      ./install_bluemix_cli

COPY ./requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
COPY . /opt/bluemix-report
RUN chmod +x /opt/bluemix-report/run.py
CMD ["python","/opt/bluemix-report/run.py"]