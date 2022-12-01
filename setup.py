#!/usr/bin/env python3
import io
import json
from pssh.clients import SSHClient
import pssh.exceptions 
import subprocess
import time
allowed_encryption = ["psk2", "none"]
allowed_radio = ['0', '1']

host = '10.15.20.1'

user_name = "root"

reconfigure_wifi = False
reconfigure_client = False
ssh = SSHClient(host, user=user_name, timeout=5, num_retries=1)

def multi_wifi_config_validator(data, name):
    index = 1
    for x in data:
        try:
            x["ssid"]
        except KeyError:
            print("No SSID for {} entry {}".format(name, index))
        try:
            x["password"]
            if len(x["password"]) < 8:
                raise ValueError("Password for {} entry {} is shorter than minimal lenght of 8".format(name, index))
        except:
            print("No password for {} entry {}. Assuming open network. Make sure it is correct.".format(name, index))
            x["password"] = none
        index += 1

def set_multi_wifi(ssid, password, priority):
    cmd = "uci add multi_wifi wifi-iface\n"
    cmd += "uci set multi_wifi.@wifi-iface[-1].ssid='{}'\n".format(ssid)
    if password != None:
        cmd += "uci set multi_wifi.@wifi-iface[-1].key='{}'\n".format(password)
    cmd += "uci set multi_wifi.@wifi-iface[-1].enabled='1'\n"
    cmd += "uci set multi_wifi.@wifi-iface[-1].priority='{}'\n".format(priority)
    return cmd

try:
    config = open("config.json",'r')
    config = json.load(config)
except:
    print("Could not load configuration file.")

#verify if wifi_ap and wifi_client configs are present and valid
cmd = ""
try:
    config["wifi_client"]
except KeyError:
    print("wifi_client section not defined, skipping client configuration")
else:
    multi_wifi_config_validator(config["wifi_client"], "wifi_client")
    priority = 1
    for x in config["wifi_client"]:
        cmd += set_multi_wifi(x["ssid"], x["password"], priority)
        priority += 1
    try:
        wifi_client_radio = config["wifi_client_radio"]
        if wifi_client_radio not in [0,1,'0','1']:
            raise TypeError("Allowed values for wifi_client_radio is 0 or 1.")
    except:
        print("wifi_client_radio not defined, assuming 2.4GHz radio")
        wifi_client_radio = 0
        
    reconfigure_multi_wifi = True

if reconfigure_multi_wifi:
    try:
        #delete multi_wifi WLANs list, write new one
        print(cmd)
        output = ssh.run_command("for x in $(seq $(expr $(uci get multi_wifi.@wifi-iface[-1].priority) - 1) -1 0); do uci delete multi_wifi.@wifi-iface[$x]; done; " + cmd + "uci commit;" + "reload_config")
        for line in output.stdout:
            print(line)
        #get current radio for multi_wifi
        output = ssh.run_command("uci get wireless.multi_wifi.device")
        used_radio = None
        for line in output.stdout:
            used_radio = line 
            print(used_radio)
        if used_radio != 'radio'+str(wifi_client_radio):
            print("uci set wireless.multi_wifi.device='radio"+str(wifi_client_radio)+"';" +"uci commit; reload_config")
            output = ssh.run_command("uci set wireless.multi_wifi.device='radio"+str(wifi_client_radio)+"';" +"uci commit; reload_config")
            for line in output.stdout:
                print(line)
    
    except pssh.exceptions.ConnectionError:
        print("SSH connection failed, configuration not applied")
    else:
        print("Router configuration saved")
    
#wait till uplink is established - checking via ping to 8.8.8.8 is successful
while subprocess.call(['ping','8.8.8.8','-c','1',"-W","1"], stdout=subprocess.DEVNULL):
    time.sleep(5)
    print("Waiting for configuration to get applied")
print("Success")

#connect to husarnet
try:
    config['husarnet']
except KeyError:
    print("Husarnet section not defined, skipping Husarnet configuration")
else:
    try:
        if config['husarnet']['join_code'] == "your_join_code":
            print("Your Husarnet joincode is incorrect, skipping Husarnet configuration")
        else:        
            subprocess.run(["sudo husarnet " + config['husarnet']['joincode'] + " " + config['husarnet']['hostname']], shell=True)
    except KeyError:
        print("Hostname or joincode not defined in husarnet configuration")


