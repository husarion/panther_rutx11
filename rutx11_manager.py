#!/usr/bin/env python3

import click
import json
import os
import requests
import subprocess


class RUTX11HTTPCommands:
    LOGIN = "/api/login"
    REBOOT = "/system/actions/reboot"
    DHCP_SERVER_LAN = "/api/dhcp/servers/ipv4/config/lan"
    DHCP_STATIC_LEASES = "/api/dhcp/static_leases/ipv4/config"
    INTERFACES = "/api/interfaces/config"
    INTERFACES_LAN = "/api/interfaces/config/lan"
    INTERFACES_WAN = "/api/interfaces/config/wan"
    WIRELESS_DEVICES = "/api/wireless/devices/config"
    WIRELESS_INTERFACES = "/api/wireless/interfaces/config"
    GPS_GLOBAL = "/api/gps/global"
    GPS_NMEA_NMEA_FORWARDING = "/api/gps/nmea/config/nmea_forwarding"
    GPS_NMEA_RULES = "/api/gps/nmea/rules/config"
    NTP_NTP_CLIENT = "/api/date_time/ntp/client/config/ntpclient"
    RMS_ACTIONS_CONNECT = "/api/rms/actions/connect"
    FIREWALL_ZONES_ID3 = "/api/firewall/zones/config/3"


class RUTX11Manager:
    def __init__(self, username: str, password: str) -> None:
        self._device_ip = "10.15.20.1"
        self._username = username
        self._password = password
        self._token = None

        self._request_url = "https://" + self._device_ip

        self._rpi_serial = self._get_rpi_serial()
        self._rpi_mac = self._get_rpi_mac()

        print("Raspberry Pi serial: ", self._rpi_serial)
        print("Raspberry Pi MAC: ", self._rpi_mac)

        self._login()

    def factory_settings(self) -> None:
        self._configure_dhcp()
        self._configure_interfaces_lan()
        self._configure_ntp_client()
        self._configure_gps()
        self._configure_nmea()
        self._configure_wireless_devices()
        self._configure_wireless_interfaces()
        self._configure_static_leases()

    def reboot(self) -> None:
        response = self._request_post(RUTX11HTTPCommands.REBOOT, {})
        if response.status_code != 200:
            print("Failed to reboot the router")

    def _get_rpi_serial(self) -> str:
        try:
            result = subprocess.run(
                ["awk", "/Serial/ {print $3}", "/proc/cpuinfo"],
                capture_output=True,
                text=True,
                check=True,
            )

            rpi_serial = result.stdout.strip()[-4:]
            if rpi_serial == "":
                raise Exception("Serial number not found")

            return rpi_serial
        except Exception as err:
            click.secho(
                f"WARNING: Failed to get Raspberry Pi serial: {err} Assigning default '0000'",
                fg="yellow",
            )
            return "0000"

    def _get_rpi_mac(self) -> str:
        try:
            result = subprocess.run(
                ["ethtool", "--show-permaddr", "eth0"], capture_output=True, text=True, check=True
            )
            return result.stdout.split()[-1].strip()
        except Exception as err:
            click.secho(
                f"WARNING: Failed to get Raspberry Pi MAC: {err} \nAssigning default '00:00:00:00:00:00'",
                fg="yellow",
            )
            return "00:00:00:00:00:00"

    def _login(self) -> None:
        url = self._request_url + RUTX11HTTPCommands.LOGIN
        data = {
            "username": self._username,
            "password": self._password,
        }

        response = requests.post(url, json=data, verify=False)
        if response.status_code != 200:
            print("Failed to connect: ", json.dumps(response.json(), indent=2))
            raise Exception("Failed to connect")

        self._token = response.json()["data"]["token"]
        print("Logged in successfully")

    def _configure_dhcp(self) -> None:
        data = {"data": {"leasetime": "12h"}}

        response = self._request_put(RUTX11HTTPCommands.DHCP_SERVER_LAN, data)
        if response.status_code != 200:
            print("Failed to configure DHCP: ", json.dumps(response.json(), indent=2))
            return

        print("DHCP configured successfully")

    def _configure_interfaces_lan(self) -> None:
        data = {
            "data": {
                "ipaddr": "10.15.20.1",
                "ifname": ["eth0", "eth1"],
            }
        }

        response = self._request_put(RUTX11HTTPCommands.INTERFACES_LAN, data)
        if response.status_code != 200:
            print("Failed to configure LAN interface: ", json.dumps(response.json(), indent=2))
            return

        print("LAN interface configured successfully")

    def _configure_interfaces_wan(self) -> None:
        data = {
            "data": {
                "enabled": "0",
            }
        }

        response = self._request_put(RUTX11HTTPCommands.INTERFACES_WAN, data)
        if response.status_code != 200:
            print("Failed to configure WAN interface: ", json.dumps(response.json(), indent=2))
            return

        print("WAN interface configured successfully")

    def _configure_interfaces_wwan(self) -> None:
        data = {
            "data": {
                "area_type": "wan",
                "id": "wwan",
                "metric": "2",
                "proto": "dhcp",
            }
        }

        response = self._request_post(RUTX11HTTPCommands.INTERFACES, data)
        if response.status_code != 201:
            print("Failed to configure WWAN interface: ", json.dumps(response.json(), indent=2))
            return

        print("WWAN interface configured successfully")

    def _configure_firewall(self):
        data = {"data": {"network": ["wan", "wan6", "mob1s1a1", "mob1s2a1", "wwan"]}}

        response = self._request_put(RUTX11HTTPCommands.FIREWALL_ZONES_ID3, data)
        if response.status_code != 200:
            print("Failed to configure firewall: ", json.dumps(response.json(), indent=2))
            return

        print("Firewall configured successfully")

    def _configure_ntp_client(self) -> None:
        data = {
            "data": {
                "enabled": "1",
                "zoneName": "Europe/Warsaw",
                "interval": "86400",
                "sync_enabled": "1",
            }
        }

        response = self._request_put(RUTX11HTTPCommands.NTP_NTP_CLIENT, data)
        if response.status_code != 200:
            print("Failed to configure NTP client: ", json.dumps(response.json(), indent=2))
            return

        print("NTP client configured successfully")

    def _configure_gps(self) -> None:
        data = {
            "data": {
                "enabled": "1",
                "galileo_sup": "1",
                "glonass_sup": "1",  # in script value is 7, but api accepts 0 or 1
                "beidou_sup": "1",  # in script value is 3, but api accepts 0 or 1
            }
        }

        response = self._request_put(RUTX11HTTPCommands.GPS_GLOBAL, data)
        if response.status_code != 200:
            print("Failed to configure GPS: ", json.dumps(response.json(), indent=2))
            return

        print("GPS configured successfully")

    def _configure_nmea(self) -> None:
        data = {
            "data": {
                "enabled": "1",
                "port": "5000",
                "proto": "udp",
                "hostname": "10.15.20.2",
            }
        }
        response = self._request_put(RUTX11HTTPCommands.GPS_NMEA_NMEA_FORWARDING, data)
        if response.status_code != 200:
            print("Failed to configure NMEA: ", json.dumps(response.json(), indent=2))
            return

        data = {
            "data": [
                {
                    "id": id,
                    "forwarding_enabled": "1",
                    "forwarding_interval": "1",
                }
                for id in [
                    "GPGSV",
                    "GPGGA",
                    "GPVTG",
                    "GPRMC",
                    "GPGSA",
                    "GLGSV",
                    "GNGSA",
                    "GNGNS",
                    "GAGSV",
                    "PQGSV",
                    "PQGSA",
                ]
            ]
        }

        response = self._request_put(RUTX11HTTPCommands.GPS_NMEA_RULES, data)
        if response.status_code != 200:
            print("Failed to configure NMEA rules: ", json.dumps(response.json(), indent=2))
            return

        print("NMEA configured successfully")

    def _configure_wireless_devices(self) -> None:
        data = {
            "data": [
                {
                    "id": id,
                    "channel": "auto",
                }
                for id in ["radio0", "radio1"]
            ]
        }

        response = self._request_put(RUTX11HTTPCommands.WIRELESS_DEVICES, data)
        if response.status_code != 200:
            print("Failed to configure wireless devices: ", json.dumps(response.json(), indent=2))
            return

        print("Wireless devices configured successfully")

    def _configure_wireless_interfaces(self) -> None:
        robot_model = os.getenv("ROBOT_MODEL", "PTH")
        prefix = "Lynx_" if robot_model == "LNX" else "Panther_"

        data = {
            "data": [
                {
                    "id": "default_radio0",
                    "ssid": prefix + self._rpi_serial,
                    "key": "husarion",
                },
                {
                    "id": "default_radio1",
                    "ssid": prefix + "5G_" + self._rpi_serial,
                    "key": "husarion",
                },
            ]
        }

        response = self._request_put(RUTX11HTTPCommands.WIRELESS_INTERFACES, data)
        if response.status_code != 200:
            print(
                "Failed to configure wireless interfaces: ", json.dumps(response.json(), indent=2)
            )
            return

        print("Wireless interfaces configured successfully")

    def _configure_multi_ap_interface(self) -> None:
        data = {
            "data": {
                # "id": "wifi-iface",
                "network": "wwan",
                "device": "radio0",
                "mode": "multi_ap",
                "enabled": "1",
                "scan_time": "30",
            }
        }

        response = self._request_post(RUTX11HTTPCommands.WIRELESS_INTERFACES, data)
        if response == 201:
            print("Failed to configure Multi AP interface: ", json.dumps(response.json(), indent=2))
            return

        print("Multi AP interface configured successfully")

    def _configure_static_leases(self) -> None:
        data = {
            "data": {
                "id": "host",
                "ip": "10.15.20.2",
                "mac": self._rpi_mac,
                "name": "rpi",
            },
        }

        response = self._request_post(RUTX11HTTPCommands.DHCP_STATIC_LEASES, data)
        if response.status_code != 200:
            print("Failed to configure static leases: ", json.dumps(response.json(), indent=2))
            return

        print("Static leases configured successfully")

    def _request_get(self, command: str, data: dict) -> requests.Response:
        url = self._request_url + command
        headers = {"Authorization": "Bearer " + self._token}
        return requests.get(url, headers=headers, json=data, verify=False)

    def _request_put(self, command: str, data: dict) -> requests.Response:
        url = self._request_url + command
        headers = {"Authorization": "Bearer " + self._token}
        return requests.put(url, headers=headers, json=data, verify=False)

    def _request_post(self, command: str, data: dict) -> requests.Response:
        url = self._request_url + command
        headers = {"Authorization": "Bearer " + self._token}
        return requests.post(url, headers=headers, json=data, verify=False)


import argparse


def main(args=None):
    parser = argparse.ArgumentParser(description="RUTX11 Manager")
    parser.add_argument("--restore-default", action="store_false", help="Restore default settings")
    parsed_args = parser.parse_args(args)

    username = input("Enter the username: ")
    password = input("Enter the password: ")
    manager = RUTX11Manager(username=username, password=password)

    if parsed_args.restore_default:
        manager.factory_settings()
        manager.reboot()
        return


if __name__ == "__main__":
    main()
