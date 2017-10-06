# based on image python 2.7
FROM python:2.7

ENV BXREPORT_HOME=/opt/bluemix-report

#RUN wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | apt-key add - &&\
#    echo "deb http://packages.cloudfoundry.org/debian stable main" | tee /etc/apt/sources.list.d/cloudfoundry-cli.list

#RUN wget https://s3-us-west-1.amazonaws.com/cf-cli-releases/releases/v6.23.1/cf-cli-installer_6.23.1_x86-64.deb &&\
#    dpkg -i cf-cli-*.deb && apt-get install -f

RUN wget http://public.dhe.ibm.com/cloud/bluemix/cli/bluemix-cli/latest/Bluemix_CLI_amd64.tar.gz -O Bluemix_CLI.tar.gz && \
      tar -xvf Bluemix_CLI.tar.gz && \
      cd Bluemix_CLI && \
      ./install_bluemix_cli

# indicate the working directory for RUN, CMD, ENTRYPOINT
WORKDIR ${BXREPORT_HOME}

# copy files to Docker
ADD . ${BXREPORT_HOME}

RUN pip install -r requirements.txt
RUN chmod +x run.py

# Vulnerability Advisor : Fix PASS_MAX_DAYS, PASS_MIN_DAYS and PASS_MIN_LEN, common-password
RUN mv -f /etc/login.defs /etc/login.defs.orig
RUN sed 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS 90/' /etc/login.defs.orig > /etc/login.defs
RUN grep -q '^PASS_MIN_DAYS' /etc/login.defs && sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS 1/' /etc/login.defs || echo 'PASS_MIN_DAYS 1\n' >> /etc/login.defs
RUN grep -q '^PASS_MIN_LEN' /etc/login.defs && sed -i 's/^PASS_MIN_LEN.*/PASS_MIN_LEN 8/' /etc/login.defs || echo 'PASS_MIN_LEN 9\n' >> /etc/login.defs
RUN grep -q '^password.*required' /etc/pam.d/common-password && sed -i 's/^password.*required.*/password    required            pam_permit.so minlen=9/' /etc/pam.d/common-password || echo 'password    required            pam_permit.so minlen=9' >> /etc/pam.d/common-password


# default docker execution command
CMD ["./run.py","80", "prod"]
