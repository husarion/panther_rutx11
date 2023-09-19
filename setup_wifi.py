#!/usr/bin/env python3

# Script for changing MultiAP WiFi settings in Teltonika RUTX11.
# Requires RUTX11 device with configuration set by factory_settings.sh script - by default done by Husarion during production.  

from click import secho
import io
import json
import os
from pssh.clients import SSHClient
import pssh.exceptions 
import subprocess
import sys
import time


allowed_radio = ['0', '1']

host = '10.15.20.1' # IP adress of RUTX11
user_name = "root"
config_file = 'config.json' 
reconfigure_wifi = False
reconfigure_client = False
debug_flag = False # if true print debug messages

ssh = SSHClient(host, user=user_name, timeout=5, num_retries=1)

def multi_wifi_config_validator(data, name):
    for index, key in enumerate(data, start=1):
        try:
            if key["ssid"] == '':
                raise KeyError
            
        except KeyError:
            secho("No SSID for {} entry {}".format(name, index), fg='red', bold=True)
            sys.exit("Exiting.")
        try:
            key["password"]
            if len(key["password"]) < 8:
                if key["password"] == '':
                    secho("No password for {} entry {}. Assuming open network. Make sure it is correct.".format(name, index))
                    key["password"] = None
                else:
                    raise ValueError("Password for {} entry {} is shorter than minimal lenght of 8".format(name, index))
                
        except ValueError as e:
            secho(e, fg='red', bold=True)
            sys.exit("Exiting.")
        except KeyError:
            secho("No password for {} entry {}. Assuming open network. Make sure it is correct.".format(name, index), fg='yellow', bold=True)
            key["password"] = None

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
    secho("Could not load configuration file.", fg='red', bold=True)
    sys.exit("Exiting.")

# Verify if wifi_client config is present and valid
cmd = ""
try:
    config["wifi_client"]
except KeyError:
    secho("wifi_client section not defined, skipping client configuration")
else:
    multi_wifi_config_validator(config["wifi_client"], "wifi_client")
    for priority, key in enumerate(config["wifi_client"], start=1):
        cmd += set_multi_wifi(key["ssid"], key["password"], priority)
    if debug_flag == True:
        secho(cmd)
    try:
        wifi_client_radio = config["wifi_client_radio"]
        if wifi_client_radio not in [0,1,'0','1']:
            raise TypeError("Allowed values for wifi_client_radio is 0 or 1.")
            sys.exit("Exiting.")

    except KeyError:
        secho("wifi_client_radio not defined, assuming 2.4GHz radio", fg='yellow')
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
                secho(used_radio)
        if used_radio != 'radio' + str(wifi_client_radio):
            cmd += "uci set wireless.multi_wifi.device='radio" + str(wifi_client_radio) + "';"
            if debug_flag == True:
                secho("Changing radio")
        # Delete multi_wifi WLANs list, write new one
        output = ssh.run_command("for x in $(seq $(expr $(uci get multi_wifi.@wifi-iface[-1].priority) - 1) -1 0); do uci delete multi_wifi.@wifi-iface[$x]; done; " + cmd + "uci commit;" + "reload_config")
        time.sleep(3)
    except pssh.exceptions.ConnectionError:
        secho("SSH connection failed, configuration not applied", fg='red', bold=True)
        sys.exit("Exiting.")
    else:
        secho("Router configuration saved")
    
# Wait till uplink is established - checking via ping to 8.8.8.8 is successful
# Wait 10 seconds to allow router reconfiguration
secho("Pinging 8.8.8.8 to check for internet connection. It can take up to 8 minutes (depending on choosen radio).", fg='yellow', bold=True)
time.sleep(10)
try_count = 1
auth_fail_time = None
kernel_time = None
while subprocess.call(['ping','8.8.8.8','-c','1',"-W","1"], stdout=subprocess.DEVNULL):
    time.sleep(10)
    secho("Waiting for establishing internet connection. Try {}/50".format(try_count))
    try_count += 1

    if try_count > 50:
        secho("Failed to obtain internet connection. \nCheck if choosen WiFi is in range and/or SSID is correct.", fg='red', bold=True)
        sys.exit("Exiting")
    try:
        output = ssh.run_command("cat /proc/uptime | awk '{print $1}'")
        kernel_time = None
        for line in output.stdout:
            kernel_time = line
        output = ssh.run_command("dmesg | grep 'denied authentication (status 1)' | tail -1 | awk '{print $2}'")
        for line in output.stdout:
            auth_fail_time = line
        if debug_flag == True:
            secho(kernel_time)
            secho(auth_fail_time)
    except pssh.exceptions.ConnectionError:
        secho("SSH connection failed, configuration not applied", fg='red', bold=True)
        sys.exit("Exiting.")            
    if auth_fail_time != None:
        auth_fail_time = auth_fail_time[:-1]
    else:
        continue
    if float(auth_fail_time) > float(kernel_time) - 15:
         secho("Failed to obtain internet connection.\nPassword is incorrect.", fg='red', bold=True)
         sys.exit()
secho("Success. Panther has internet connection.", fg='green', bold=True)

# Connect to husarnet
try:
    config['husarnet']
except KeyError:
    secho("Husarnet section not defined, skipping Husarnet configuration")
else:
    try:
        if config['husarnet']['join_code'] == "your_join_code":
            secho("Your Husarnet joincode is incorrect, skipping Husarnet configuration")
        else:        
            subprocess.run(["sudo husarnet " + config['husarnet']['joincode'] + " " + config['husarnet']['hostname']], shell=True)
    except KeyError:
        secho("Hostname or joincode not defined in husarnet configuration")



