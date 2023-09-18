#!/usr/bin/env python3

# Script for changing MultiAP WiFi settings in Teltonika RUTX11.
# Requires RUTX11 device with configuration set by first_setup.sh script - by default done by Husarion during production.  

import io
import json
from pssh.clients import SSHClient
import pssh.exceptions 
import subprocess
import time
import os
import sys

allowed_radio = ['0', '1']

host = '10.15.20.1' # IP adress of RUTX11
user_name = "root"
config_file = 'config.json' 
reconfigure_wifi = False
reconfigure_client = False
debug_flag = True # if true print debug messages

ssh = SSHClient(host, user=user_name, timeout=5, num_retries=1)

def multi_wifi_config_validator(data, name):
    index = 1
    for x in data:
        try:
            if x["ssid"] == '':
                raise KeyError
            
        except KeyError:
            print("No SSID for {} entry {}".format(name, index))
            sys.exit("Exiting.")
        try:
            x["password"]
            if len(x["password"]) < 8:
                if x["password"] == '':
                    print("No password for {} entry {}. Assuming open network. Make sure it is correct.1".format(name, index))
                    x["password"] = None
                else:
                    raise ValueError("Password for {} entry {} is shorter than minimal lenght of 8".format(name, index))
                
        except ValueError as e:
            print(e)
            sys.exit("Exiting.")
        except KeyError:
            print("No password for {} entry {}. Assuming open network. Make sure it is correct.2".format(name, index))
            x["password"] = None
        index += 1

def set_multi_wifi(ssid, password, priority):
    command = "uci add multi_wifi wifi-iface\n"
    command += "uci set multi_wifi.@wifi-iface[-1].ssid='{}'\n".format(ssid)
    if password != None:
        command += "uci set multi_wifi.@wifi-iface[-1].key='{}'\n".format(password)
    command += "uci set multi_wifi.@wifi-iface[-1].enabled='1'\n"
    command += "uci set multi_wifi.@wifi-iface[-1].priority='{}'\n".format(priority)
    return command


# Loading configuration file
try:
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
    config = open(path,'r')
    config = json.load(config)
except:
    print("Could not load configuration file.")
    sys.exit("Exiting.")

# Verify if wifi_client config is present and valid
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
    if debug_flag == True:
        print(cmd)
    try:
        wifi_client_radio = config["wifi_client_radio"]
        if wifi_client_radio not in [0,1,'0','1']:
            raise TypeError("Allowed values for wifi_client_radio is 0 or 1.")
            sys.exit("Exiting.")

    except KeyError:
        print("wifi_client_radio not defined, assuming 2.4GHz radio")
        wifi_client_radio = 0
        
    reconfigure_multi_wifi = True

if reconfigure_multi_wifi:
    try:
        # Get current radio for multi_wifi
        output = ssh.run_command("uci get wireless.multi_wifi.device")
        used_radio = None
        for line in output.stdout:
            used_radio = line
            if debug_flag == True:    
                print(used_radio)
        if used_radio != 'radio'+str(wifi_client_radio):
            cmd +="uci set wireless.multi_wifi.device='radio"+str(wifi_client_radio)+"';"
            if debug_flag == True:
                print("Changing radio")
        # Delete multi_wifi WLANs list, write new one
        output = ssh.run_command("for x in $(seq $(expr $(uci get multi_wifi.@wifi-iface[-1].priority) - 1) -1 0); do uci delete multi_wifi.@wifi-iface[$x]; done; " + cmd + "uci commit;" + "reload_config")
        time.sleep(3)
    except pssh.exceptions.ConnectionError:
        print("SSH connection failed, configuration not applied")
        sys.exit("Exiting.")
    else:
        print("Router configuration saved")
    
# Wait till uplink is established - checking via ping to 8.8.8.8 is successful
# Wait 10 seconds to allow router reconfiguration
print("Pinging 8.8.8.8 to check for internet connection. It can take up to 3 minutes (depending on choosen radio).")
time.sleep(10)
while subprocess.call(['ping','8.8.8.8','-c','1',"-W","1"], stdout=subprocess.DEVNULL):
    time.sleep(10)
    print("Waiting for establishing internet connection.")
print("Success. Panther has internet connection.")

# Connect to husarnet
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



