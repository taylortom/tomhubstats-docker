from datetime import datetime
import gpiozero
import json
import math
import os
import paho.mqtt.client as mqtt
import platform
import psutil
import socket
import subprocess
import time

class MQTT:
  def __init__(self, broker, username, password, topic):
    self.client = mqtt.Client(topic)
    self.client.username_pw_set(username, password)
    self.client.on_disconnect = on_disconnect
    self.client.connect(broker)
    self.topic = topic

  def publish(self):
    try:
      data = get_data()
      # print(json.dumps(data, indent=2))
      self.client.publish(self.topic, json.dumps(data))
    except Exception as e:
      print(e)
      # self.client.reconnect()
      # self.publish()


  def reconnect(self):
    try:
      self.client.reconnect()
    except:
      time.sleep(5)
      self.reconnect()

def on_disconnect(client, userdata, rc):
  client.reconnect()

def get_data():
  data = {};
  data["last_boot_time"] = "{}".format(datetime.fromtimestamp(psutil.boot_time()))
  data["up_time"] = get_uptime()
  data["ip_address"] = socket.gethostbyname(socket.gethostname())
  # CPU
  cpu_freq = psutil.cpu_freq()
  data["cpu_cores"] = psutil.cpu_count(logical=False)
  data["cpu_threads"] = psutil.cpu_count()
  data["cpu_max_freq"] = round(cpu_freq.max)
  data["cpu_min_freq"] = round(cpu_freq.min)
  data["cpu_freq"] = cpu_freq.current
  data["cpu_usage"] = psutil.cpu_percent()
  data["cpu_temp"] = round(gpiozero.CPUTemperature().temperature, 1)
  # RAM
  svmem = psutil.virtual_memory()
  data["ram_total"] = convert_bytes(svmem.total)
  data["ram_used"] = convert_bytes(svmem.used)
  data["ram_used_percent"] = svmem.percent
  data["ram_available"] = convert_bytes(svmem.available)
  # Disk
  st = os.statvfs("/")
  data["disk_total"] = convert_bytes(st.f_blocks * st.f_frsize)
  data["disk_used"] = convert_bytes((st.f_blocks - st.f_bfree) * st.f_frsize)
  data["disk_used_percent"] = round(((st.f_blocks - st.f_bfree) / float(st.f_blocks))*100, 1)
  data["disk_free"] = convert_bytes(st.f_bavail * st.f_frsize)

  st = os.statvfs("/media/multimedia")
  data["media_total"] = convert_bytes(st.f_blocks * st.f_frsize)
  data["media_used"] = convert_bytes((st.f_blocks - st.f_bfree) * st.f_frsize)
  data["media_used_percent"] = round(((st.f_blocks - st.f_bfree) / float(st.f_blocks))*100, 1)
  data["media_free"] = convert_bytes(st.f_bavail * st.f_frsize)

  return data;

def get_uptime():
  process = subprocess.Popen(["uptime", "-p"], stdout=subprocess.PIPE)
  output, error = process.communicate()
  return output[3:-1]

def convert_bytes(size_bytes):
  if size_bytes == 0:
    return "0B"
  size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
  i = int(math.floor(math.log(size_bytes, 1024)))
  p = math.pow(1024, i)
  return "%s %s" % (round(size_bytes / p, 2), size_name[i])

mqttInstance = MQTT(os.environ['MQTT_SERVER_URL'], os.environ['MQTT_USER'], os.environ['MQTT_PASS'], os.environ['MQTT_SENSOR_NAME'])

while True:
  mqttInstance.publish()
  time.sleep(int(os.environ["MQTT_INTERVAL"]))
