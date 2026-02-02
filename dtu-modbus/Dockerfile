ARG BUILD_FROM=homeassistant/amd64-base-python:3.10-alpine3.18
FROM $BUILD_FROM

RUN pip3 install --no-cache-dir \
    hoymiles_modbus==0.9.1 \
    paho-mqtt==1.6.1

COPY main.py const.py /app/

# s6-overlay v3 service definition
COPY run.sh /etc/s6-overlay/s6-rc.d/hoymiles/run
RUN chmod a+x /etc/s6-overlay/s6-rc.d/hoymiles/run \
    && echo "longrun" > /etc/s6-overlay/s6-rc.d/hoymiles/type \
    && mkdir -p /etc/s6-overlay/s6-rc.d/user/contents.d \
    && touch /etc/s6-overlay/s6-rc.d/user/contents.d/hoymiles
