#!/bin/bash

#Script used for first setup of Teltonika RUTX11 

rutx11_ip=192.168.1.1

while [ "$1" != "" ]; do
    case $1 in
        -a | --address )        shift
                                rutx11_ip="$1"
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done
#get serial number of Raspberry Pi
rpi_serial=$(cat /proc/cpuinfo | awk '/Serial/ {print $3}')
#get MAC of eth on Raspberry PI
rpi_mac=$(ethtool --show-permaddr eth0 | awk '{print $3}')
#get MAC of NUC
ping nuc -c 1
nuc_mac=$(arp -a | awk '/nuc/ {print $4}')
	
#create ssh private/public key pair without passphrase
ssh-keygen -t rsa -b 4096 -q -N "" -f ~/.ssh/id_rsa

#copy public key to RUTX11
#human input of password is required
ssh root@$rutx11_ip "tee -a /etc/dropbear/authorized_keys" < ~/.ssh/id_rsa.pub

#set config on RUTX11
ssh root@$rutx11_ip << EOF
    uci set dhcp.lan.time='12' 
    uci set dhcp.lan.letter='h'
    uci set network.lan.ipaddr='10.15.20.1'

    uci set network.wan.auto='0'
    uci set network.lan.ifname='eth0 eth1'

    uci set ntpclient.@ntpclient[0].zoneName='Europe/Warsaw'  
    uci set system.system.timezone='CET-1CEST,M3.5.0,M10.5.0/3'
    uci set system.ntp.enabled='1'

    uci set rms_connect_mqtt.rms_connect_mqtt.enable='0'

    uci set gps.gpsd.enabled='1'
    uci set gps.gpsd.galileo_sup='1'
    uci set gps.gpsd.glonass_sup='1'
    uci set gps.gpsd.beidou_sup='0'
    
    uci set gps.nmea_forwarding.enabled='1'
    uci set gps.nmea_forwarding.hostname='10.15.20.3'
    uci set gps.nmea_forwarding.port='5000'
    uci set gps.nmea_forwarding.proto='udp'

    uci set gps.https.enabled='1'
    uci set gps.https.hostname='10.15.20.3'

    uci set gps.GPGSV.forwarding_enabled='0'
    uci set gps.GPGSV.forwarding_interval='1'
    uci set gps.GPGGA.forwarding_enabled='0'
    uci set gps.GPGGA.forwarding_interval='1'
    uci set gps.GPVTG.forwarding_enabled='0'
    uci set gps.GPVTG.forwarding_interval='1'
    uci set gps.GPRMC.forwarding_enabled='0'
    uci set gps.GPRMC.forwarding_interval='1'
    uci set gps.GPGSA.forwarding_enabled='0'
    uci set gps.GPGSA.forwarding_interval='1'
    uci set gps.GLGSV.forwarding_enabled='0'
    uci set gps.GLGSV.forwarding_interval='1'
    uci set gps.GNGSA.forwarding_enabled='0'
    uci set gps.GNGSA.forwarding_interval='1'
    uci set gps.GNGNS.forwarding_enabled='0'
    uci set gps.GNGNS.forwarding_interval='1'
    uci set gps.GAGSV.forwarding_enabled='0'
    uci set gps.GAGSV.forwarding_interval='1'
    uci set gps.PQGSV.forwarding_enabled='0'
    uci set gps.PQGSV.forwarding_interval='1'
    uci set gps.PQGSA.forwarding_enabled='0'
    uci set gps.PQGSA.forwarding_interval='1'    

    uci set wireless.radio0.channel='auto'
    uci set wireless.default_radio0.ssid='Panther_${rpi_serial: -4}'
    uci set wireless.default_radio0.key='husarion'
    uci set wireless.radio1.channel='auto'
    uci set wireless.default_radio1.ssid='Panther_5G_${rpi_serial: -4}'
    uci set wireless.default_radio1.key='husarion'

    uci add dhcp host
    uci set dhcp.@host[-1].ip="10.15.20.2"
    uci set dhcp.@host[-1].mac="$rpi_mac"
    uci set dhcp.@host[-1].name="rpi"

    uci add dhcp host
    uci set dhcp.@host[-1].ip="10.15.20.3"
    uci set dhcp.@host[-1].mac="$nuc_mac"
    uci set dhcp.@host[-1].name="nuc"
    uci commit
    reboot
    
EOF




