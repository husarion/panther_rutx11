#!/bin/bash
#Script used to connect to wifi network as a WAN connection

rutx11_ip=10.15.20.1
function help {
    echo "
    Add WiFi network as a WAN for RUTX11. Possible on 2.4GHz and 5GHz radios. Currently only single AP (no roaming) per radio supported. Choosen radio will switch its channel to the same as added WiFi. 
    WiFi AP which you wish to add must be in range of RUTX11. 
    Usage: sta_mode [-abcehprs] 
    Options: 

    -r, --radio <radio_numer> 0 for 2.4GHz radio, 1 for 5GHz radio 
    -s, --ssid <SSID> SSID (name) of WiFi network to be added. It must be in range of RUTX11 when command is run!
    -p, --password <password> password for WiFi network. If network is open not required.
    OPTIONAL -b, --bssid <BSSID> MAC address of AP which broadcast WiFi network. If not given network scan will be initiated to find it.
    OPTIONAL -e, --encryption <string> psk2 for WPA2, psk for WPA, wep for WEP, none if open WiFi. If not given network scan will be initiated to find it.
    OPTIONAL -a, --address <ip> IP4 address of RUTX11. If not given default value 10.15.20.1 will be used
    -h, --help
    Example: 
    In order to connect to 'MyWiFi' on 2.4GHZ with 'Password' execute:
    ./sta_mode.sh -r 0 -s MyWiFi -p Password"
    
}
if [[ $# -eq 0 ]] ; then
    help
    exit
fi
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
        -p | --password )       shift
                                password="$1"
                                ;;
        -b | --bssid )          shift
                                bssid="$1"
                                ;;
        -e | --encryption )     shift
                                encryption="$1"
                                ;;
        -h | --help )           help
                                exit
                                ;;
        * )                     help
                                exit 1
    esac
    shift
done
#It's not possible to scan on enabled 5GHz interface
if [ -z ${radio+x} ]; then
echo "No radio choosen. Exiting"
exit 1
elif [ -z ${ssid+x} ]; then
echo "No SSID choosen. Exiting"
exit 1
fi
if [ "$radio" -eq 1 ]; then 
    ssh root@rutx11_ip -T <<EOF > /dev/null 2>&1
    uci set wireless.radio$radio.disabled='1'
    uci commit
    /etc/inti.d/network reload
EOF
fi
sleep 10
radio_scan=$(ssh root@$rutx11_ip -T "iwinfo radio$radio scan")
radio_scan=$(ssh root@$rutx11_ip -T "iwinfo radio$radio scan")
bssid=$(grep -A 3 -B 1 -w $ssid <<< $radio_scan | awk '/Address/ {print $5}')
channel=$(grep -A 3 -B 1 -w $ssid  <<< $radio_scan | awk '/Channel/ {print $4}')
if [ "$bssid" = "" ]; then
echo "Given SSID not found"
echo "No networks were added"
if [ "$radio" -eq 1 ]; then 
    ssh root@rutx11_ip -T <<EOF > /dev/null 2>&1
    uci set wireless.radio$radio.disabled='0'
    uci commit
    /etc/inti.d/network reload
EOF
fi
exit 1
fi
encryption_search=$(grep -A 3 -B 1 -w $ssid  <<< $radio_scan | awk ' /Encryption/ {print $2}')
encryption_search=${encryption_search%%$'\n'*}
if [ "$encryption_search" = "mixed" ]; then
encryption="psk2"
elif  [ "$encryption_search" = "WPA2" ]; then
encryption="psk2"
elif  [ "$encryption_search" = "WPA" ]; then
encryption="psk"
elif  [ "$encryption_search" = "WEP" ]; then
encryption="wep"
elif  [ "$encryption_search" = "none" ]; then
encryption="none"
fi

#if multiple APs detected take only first line (strongest signal)
bssid=${bssid%%$'\n'*}
channel=${channel%%$'\n'*}

wan_interfaces=$(ssh root@$rutx11_ip "uci get firewall.@zone[1].network")
num_wwan=$(echo $wan_interfaces | awk '{print gsub(/'wwan'/, "")}') 
if [ "$num_wwan" -eq 0 ]; then 
    interface="wwan"    
else 
    interface="wwan$num_wwan"
fi

echo "Network added"
ssh root@$rutx11_ip -T <<EOF > /dev/null 2>&1

uci set wireless.radio$radio.disabled='0'
uci set wireless.radio$radio.channel='$channel'
uci add wireless wifi-iface
uci set wireless.@wifi-iface[-1].network='$interface'
uci set wireless.@wifi-iface[-1].ssid='$ssid'
uci set wireless.@wifi-iface[-1].encryption='$encryption'
uci set wireless.@wifi-iface[-1].device='radio$radio'
uci set wireless.@wifi-iface[-1].mode='sta'
uci set wireless.@wifi-iface[-1].bssid='$bssid'
uci set wireless.@wifi-iface[-1].key='$password'

uci set network.$interface=interface
uci set network.$interface.metric='2'
uci set network.$interface.proto='dhcp'
 
uci set firewall.@zone[1].network='$wan_interfaces $interface'
uci commit
/etc/init.d/network reload && /etc/init.d/firewall reload
EOF