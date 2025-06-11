docker run -d -p 11883:1883 -p 19001:9001 \
  -v "/opt/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf" \
  -v "/opt/mosquitto/data:/mosquitto/data" \
  -v "/opt/mosquitto/log:/mosquitto/log" \
  --name mosquitto \
  eclipse-mosquitto
