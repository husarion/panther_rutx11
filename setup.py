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

phy_radio_config = (
    #radio0
    "set wireless.radio0=wifi-device\n" \
    "set wireless.radio0.type='mac80211'\n" \
    "set wireless.radio0.hwmode='11g'\n" \
    "set wireless.radio0.path='platform/soc/a000000.wifi'\n" \
    "set wireless.radio0.htmode='HT20'\n" \
    "set wireless.radio0.country='US'\n" \
    "set wireless.radio0.channel='auto'\n" \
    #radio1 
    "set wireless.radio1=wifi-device\n" \
    "set wireless.radio1.type='mac80211'\n" \
    "set wireless.radio1.hwmode='11a'\n" \
    "set wireless.radio1.path='platform/soc/a800000.wifi'\n" \
    "set wireless.radio1.htmode='VHT80'\n" \
    "set wireless.radio1.country='US'\n" \
    "set wireless.radio1.channel='auto'\n")

reconfigure_wifi = False
ssh = SSHClient(host, user=user_name, timeout=5, num_retries=1)

def wifi_config_validator(data, name):
    index = 1
    for x in data:
        try:
            x["ssid"]
        except KeyError:
            print("No SSID for {} entry {}".format(name, index))
            
        try: 
            x["radio"]
        except KeyError:
            print("Radio not choosen for {} entry {}".format(name, index))
            
        try: 
            x["encryption"]
        except KeyError:
            print("Encryption not choosen for {} entry {}".format(name, index))
            
        if x["encryption"] not in allowed_encryption:
            raise ValueError("Invalid encryption type choosen for {} entry {} \n Valid options are: ".format(name, index)) 
        if x["radio"] not in allowed_radio:
            raise ValueError("Invalid radio choosen for {} entry {} \n Valid options are 0 for 2.4GHz or 1 for 5GHz".format(name, index))
        if x["encryption"] != "none" and len(x["password"]) < 8:
            raise ValueError("Password for {} entry {} is shorter than minimal lenght of 8".format(name, index))
        index += 1

def get_radio(ifname, ssh):
    cmd =("uci get wireless.{0}.ssid;" + "uci get wireless.{0}.encryption;" + "uci get wireless.{0}.key;").format(ifname)
    output = ssh.run_command(cmd)
    ap_config = {
        "ssid":"",
        "encryption":"",
        "password":""
    }
    for line, x in zip(output.stdout, ('ssid', 'encryption', 'password')):
        ap_config[x] = line
    return ap_config

def set_radio(ifname, network, mode, radio, ssid, encryption, password="", disabled = 0):
    if ifname != None:
        cmd ="set wireless.default_radio{}=wifi-iface\n".format(radio)
    else:
        cmd = "add wireless wifi-iface\n" 
    cmd = cmd + ("set wireless.@wifi-iface[-1].network='{}'\n" \
        "set wireless.@wifi-iface[-1].device='radio{}'\n" \
        "set wireless.@wifi-iface[-1].mode='{}'\n" \
        "set wireless.@wifi-iface[-1].ssid='{}'\n" \
        "set wireless.@wifi-iface[-1].encryption='{}'\n" \
        "set wireless.@wifi-iface[-1].key='{}'\n" \
        "set wireless.@wifi-iface[-1].disabled='{}'\n").format(network, radio, mode, ssid, encryption, password, disabled)
    return cmd
try:
    config = open("config.json",'r')
    config = json.load(config)
except:
    print("Could not load configuration file")

#verify if wifi_ap and wifi_client configs are present and valid
cmd = ""
try:
    config["wifi_ap"]
except KeyError:
    print("wifi_ap section not defined, skipping AP configuration")
    #getting old AP config from router to keep it
    ap_0 = get_radio("default_radio0", ssh)
    ap_1 = get_radio("default_radio1", ssh)
    cmd += set_radio(True, "lan", "ap",'0', ap_0["ssid"], ap_0['encryption'], ap_0["password"])
    cmd += set_radio(True, "lan", "ap",'1', ap_1["ssid"], ap_1['encryption'], ap_1["password"])
else:
    wifi_config_validator(config["wifi_ap"], "wifi_ap")
    for x in config["wifi_ap"]:
        cmd += set_radio(True, "lan", "ap", x["radio"], x["ssid"], x["encryption"], x["password"])
    reconfigure_wifi = True

try:
    config["wifi_client"]
except KeyError:
    print("wifi_client section not defined, skipping client configuration")
else:
    wifi_config_validator(config["wifi_client"], "wifi_client")
    for x in config["wifi_client"]:
        cmd += set_radio(None, "trm_wwan", "sta", x["radio"], x["ssid"], x["encryption"], x["password"], 1)
    reconfigure_wifi = True

#reconfigure wifi if required
if reconfigure_wifi == True:
    cmd = "uci batch <<EOF\n" + phy_radio_config + cmd + "commit\n" + "EOF>>;"
    try:
        #delete wireless config, write new and reload wifi interface
        output = ssh.run_command("rm /etc/config/wireless;" + "touch /etc/config/wireless;" + cmd + "/etc/init.d/network reload")
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
        if config['husarnet']['joincode'] == "your_join_code":
            print("Your Husarnet joincode is incorrect, skipping Husarnet configuration")
        else:        
            subprocess.run(["sudo husarnet " + config['husarnet']['joincode'] + " " + config['husarnet']['hostname']], shell=True)
    except KeyError:
        print("Hostname or joincode not defined in husarnet configuration")


