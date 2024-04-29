FROM sysdig/sysdig:0.34.1

COPY usherlock_collector.py /usherlock_collector

RUN yum update -y \
    && yum install python3 -y \
    && yum install python3-pip -y \
    && pip3 install --upgrade pip \
    && pip3 install redis \
    && chmod +x /usherlock_collector