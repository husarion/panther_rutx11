#!/bin/bash
#Script used to connect to wifi network as a WAN connection

rutx11_ip=192.168.1.1
function help {
    echo "
    Add WiFi network as a WAN for RUTX11. Possible on 2.4GHz and 5GHz radios. Currently only single AP (no roaming) per radio supported. Choosen radio will switch its channel to the same as added WiFi. \n
    Wifi AP which you wish to add should be in range of RUTX11. \n
    Usage: sta_mode [-abcehprs] \n
    Options: \n
    \t-a, --address <ip> IP4 address of RUTX11 \n
    \t-r, --radio <radio_numer> 0 for 2.4GHz radio, 1 for 5GHz radio \n
    \t-s, --ssid <SSID> SSID (name) of WiFi network to be added. It must be in range of RUTX11 when command is run!\n
    \t-p, --password <password> password for WiFi network. If network is open not required.\n
    \t-b, --bssid <BSSID> optional, MAC address of AP which broadcast WiFi network. If not given network scan will be initiated to find it.\n
    \t-e, --encryption <string> optional, psk2 for WPA2, psk for WPA, wep for WEP, none if open WiFi. If not given network scan will be initiated to find it.\n
    \t-c, --channel <number> opntional, channel of WiFi network to be connected.  If not given network scan will be initiated to find it.\n
    \t-h, --help"
    
}

while [ "$1" != "" ]; do
    case $1 in
        -a | --address )        shift
                                rutx11_ip="$1"
                                ;;
        -r | --radio )          shift
                                radio="$1"
                                ;;
        -s | --ssid )           shift
                                ssid="$1"
                                ;;
        -p | --password )     shift
                                password="$1"
                                ;;
        -b | --bssid )     shift
                                bssid="$1"
                                ;;
        -e | --encryption )     shift
                                encryption="$1"
                                ;;
        -c | --channel )        shift
                                channel="$1"
                                ;;
        -h | --help )           help
                                exit 1
                                ;;
        * )                     help
                                exit 1
    esac
    shift
done


radio_scan=$(ssh root@$rutx11_ip "iwinfo radio$radio scan")
bssid=$(echo $radio_scan | grep -A 3 -B 1 $ssid | awk '/Address/ {print $5}')
channel=$(echo $radio_scan | grep -A 3 -B 1 $ssid | awk '/Channel/ {print $4}')
wan_interfaces=$(ssh root@$rutx11_ip "uci get firewall.@zone[1].network")
num_wwan=$(echo $wan_interfaces | awk '{print gsub(/'wwan'/, "")}') 
if [ "$num_wwan" -eq 0 ]; then 
    interface="wwan"
else 
    interface="wwan$num_wwan"
fi

ssh root@$rutx11_ip <<EOF

uci set wireless.radio$radio.disabled='0'
uci set wireless.radio$radio.channel='$channel'
uci add wireless wifi-iface
uci set wireless.@wifi-iface[-1].network='$interface'
uci set wireless.@wifi-iface[-1].ssid='$ssid'
uci set wireless.@wifi-iface[-1].encryption='psk2'
uci set wireless.@wifi-iface[-1].device='radio$radio'
uci set wireless.@wifi-iface[-1].mode='sta'
uci set wireless.@wifi-iface[-1].bssid='$bssid'
uci set wireless.@wifi-iface[-1].key='$password'

uci set network.$interface=interface
uci set network.$interface.metric='2'
uci set network.$interface.proto='dhcp'
 
uci set firewall.@zone[1].network='$wan_interfaces $interface'
EOF