# based on image python 2.7
FROM python:2.7

ENV BXVERSION=0.4.6_amd64 BXREPORT_HOME=/opt/bluemix-report

RUN wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | apt-key add - &&\
    echo "deb http://packages.cloudfoundry.org/debian stable main" | tee /etc/apt/sources.list.d/cloudfoundry-cli.list

RUN wget https://s3-us-west-1.amazonaws.com/cf-cli-releases/releases/v6.23.1/cf-cli-installer_6.23.1_x86-64.deb &&\
    dpkg -i cf-cli-*.deb && apt-get install -f

RUN wget http://public.dhe.ibm.com/cloud/bluemix/cli/bluemix-cli/Bluemix_CLI_$BXVERSION.tar.gz -O Bluemix_CLI.tar.gz && \
      tar -xvf Bluemix_CLI.tar.gz && \
      cd Bluemix_CLI && \
      ./install_bluemix_cli

# indicate the working directory for RUN, CMD, ENTRYPOINT
WORKDIR ${BXREPORT_HOME}

# copy files to Docker
ADD . ${BXREPORT_HOME}

RUN pip install -r requirements.txt
RUN chmod +x run.py

# default docker execution command
CMD ["./run.py","80"]
