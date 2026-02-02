ARG BUILD_FROM=homeassistant/amd64-base-python:3.10-alpine3.18
FROM $BUILD_FROM

RUN pip3 install --no-cache-dir \
    hoymiles_modbus==0.9.1 \
    paho-mqtt==1.6.1

WORKDIR /data
COPY main.py const.py /data/
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
