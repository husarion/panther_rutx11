#!/usr/bin/env python3

import click
import json
import os
import requests
import subprocess


class RUTX11HTTPCommands:
    LOGIN = "/api/login"
    REBOOT = "/api/system/actions/reboot"
    DHCP_SERVER_LAN = "/api/dhcp/servers/ipv4/config/lan"
    DHCP_STATIC_LEASES = "/api/dhcp/static_leases/ipv4/config"
    INTERFACES = "/api/interfaces/config"
    INTERFACES_LAN = "/api/interfaces/config/lan"
    INTERFACES_WAN = "/api/interfaces/config/wan"
    WIRELESS_DEVICES = "/api/wireless/devices/config"
    WIRELESS_DEVICES_GLOBAL = "/api/wireless/devices/global"
    WIRELESS_INTERFACES = "/api/wireless/interfaces/config"
    GPS_GLOBAL = "/api/gps/global"
    GPS_NMEA_NMEA_FORWARDING = "/api/gps/nmea/config/nmea_forwarding"
    GPS_NMEA_RULES = "/api/gps/nmea/rules/config"
    NTP_NTP_CLIENT = "/api/date_time/ntp/client/config/ntpclient"
    RMS_ACTIONS_CONNECT = "/api/rms/actions/connect"
    FIREWALL_ZONES_ID3 = "/api/firewall/zones/config/3"


class RUTX11Manager:
    def __init__(self, username: str, password: str, device_ip: str = "10.15.20.1") -> None:
        self._username = username
        self._password = password
        self._token = None
        self._request_url = "https://" + device_ip

        self._login()

    def factory_reset(self) -> None:
        self._configure_dhcp()
        self._configure_interfaces_wan()
        self._configure_interfaces_wwan()
        self._configure_interfaces_lan()
        self._configure_firewall()
        self._configure_ntp_client()
        self._configure_gps()
        self._configure_nmea()
        self._configure_wireless_devices()
        self._configure_wireless_interfaces()
        self._configure_multi_ap_interface()
        self._configure_static_leases()

    def reboot(self) -> None:
        success, _ = self._request_post(RUTX11HTTPCommands.REBOOT, {})
        if not success:
            click.secho("Failed to reboot the router", fg="red")

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
            click.secho(f"Failed to connect: {json.dumps(response.json(), indent=2)}", fg="red")
            raise Exception("Failed to connect")

        self._token = response.json()["data"]["token"]
        print("Logged in successfully")

    def _configure_dhcp(self) -> None:
        data = {"data": {"leasetime": "12h"}}

        success, _ = self._request_put(RUTX11HTTPCommands.DHCP_SERVER_LAN, data)
        if not success:
            click.secho("Failed to configure DHCP.", fg="red")
            return

        print("DHCP configured successfully")

    def _configure_interfaces_wan(self) -> None:
        data = {
            "data": [
                {
                    "id": id,
                    "enabled": "0",
                    "ifname": [],
                }
                for id in ["wan", "wan6"]
            ]
        }

        success, _ = self._request_put(RUTX11HTTPCommands.INTERFACES, data)
        if not success:
            click.secho("Failed to configure WAN interface.", fg="red")
            return

        print("WAN interface configured successfully")

    def _configure_interfaces_wwan(self) -> None:
        data = {
            "data": {
                "area_type": "wan",
                "id": "wwan",
                "metric": "2",
                "proto": "dhcp",
                "name": "wwan",
            }
        }

        success, _ = self._request_post(RUTX11HTTPCommands.INTERFACES, data)
        if not success:
            click.secho("Failed to configure WWAN interface.", fg="red")
            return

        print("WWAN interface configured successfully")

    def _configure_interfaces_lan(self) -> None:
        data = {
            "data": {
                "ipaddr": "10.15.20.1",
                "ifname": ["eth0", "eth1"],
            }
        }

        success, _ = self._request_put(RUTX11HTTPCommands.INTERFACES_LAN, data)
        if not success:
            click.secho("Failed to configure LAN interface.", fg="red")
            return

        print("LAN interface configured successfully")

    def _configure_firewall(self):
        data = {"data": {"network": ["wan", "wan6", "mob1s1a1", "mob1s2a1", "wwan"]}}

        success, _ = self._request_put(RUTX11HTTPCommands.FIREWALL_ZONES_ID3, data)
        if not success:
            click.secho("Failed to configure firewall.", fg="red")
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

        success, _ = self._request_put(RUTX11HTTPCommands.NTP_NTP_CLIENT, data)
        if not success:
            click.secho("Failed to configure NTP client.", fg="red")
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

        success, _ = self._request_put(RUTX11HTTPCommands.GPS_GLOBAL, data)
        if not success:
            click.secho("Failed to configure GPS.", fg="red")
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
        success, _ = self._request_put(RUTX11HTTPCommands.GPS_NMEA_NMEA_FORWARDING, data)
        if not success:
            click.secho("Failed to configure NMEA.", fg="red")
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

        success, _ = self._request_put(RUTX11HTTPCommands.GPS_NMEA_RULES, data)
        if not success:
            click.secho("Failed to configure NMEA rules.", fg="red")
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

        success, _ = self._request_put(RUTX11HTTPCommands.WIRELESS_DEVICES, data)
        if not success:
            click.secho("Failed to configure wireless devices.", fg="red")
            return

        data = {"data": {"country": "PL"}}

        success, _ = self._request_put(RUTX11HTTPCommands.WIRELESS_DEVICES_GLOBAL, data)
        if not success:
            click.secho("Failed to configure wireless devices.", fg="red")
            return

        print("Wireless devices configured successfully")

    def _configure_wireless_interfaces(self) -> None:
        rpi_serial = self._get_rpi_serial()
        robot_model = os.getenv("ROBOT_MODEL", "PTH")
        prefix = "Lynx_" if robot_model == "LNX" else "Panther_"

        data = {
            "data": [
                {
                    "id": "default_radio0",
                    "ssid": prefix + rpi_serial,
                    "key": "husarion",
                },
                {
                    "id": "default_radio1",
                    "ssid": prefix + "5G_" + rpi_serial,
                    "key": "husarion",
                },
            ]
        }

        success, _ = self._request_put(RUTX11HTTPCommands.WIRELESS_INTERFACES, data)
        if not success:
            click.secho("Failed to configure wireless interfaces.", fg="red")
            return

        print("Wireless interfaces configured successfully")

    def _configure_multi_ap_interface(self) -> None:
        success, response = self._request_get(RUTX11HTTPCommands.WIRELESS_INTERFACES)
        if not success:
            click.secho("Failed to get wireless interfaces.", fg="red")
            return

        for iface in response.json()["data"]:
            if iface["mode"] == "multi_ap":
                print("Deleting existing Multi AP interface")
                success, _ = self._request_delete(
                    RUTX11HTTPCommands.WIRELESS_INTERFACES, {"data": [iface["id"]]}
                )
                if not success:
                    click.secho("Failed to delete existing Multi AP interface.", fg="red")
                    return
                break

        data = {
            "data": {
                "id": "wifi-iface",
                "network": "wwan",
                "device": ["radio1"],
                "mode": "multi_ap",
                "enabled": "1",
                "scan_time": "30",
            }
        }

        success, _ = self._request_post(RUTX11HTTPCommands.WIRELESS_INTERFACES, data)
        if not success:
            click.secho("Failed to configure Multi AP interface.", fg="red")
            return

        print("Multi AP interface configured successfully")

    def _configure_static_leases(self) -> None:
        success, response = self._request_get(RUTX11HTTPCommands.DHCP_STATIC_LEASES)
        if not success:
            click.secho("Failed to get static leases.", fg="red")
            return

        data_delete = {"data": [lease["id"] for lease in response.json()["data"]]}
        success, _ = self._request_delete(RUTX11HTTPCommands.DHCP_STATIC_LEASES, data_delete)
        if not success:
            click.secho("Failed to delete static leases.", fg="red")
            return

        data = {
            "data": {
                "ip": "10.15.20.2",
                "mac": self._get_rpi_mac(),
                "name": "rpi",
            },
        }

        success, _ = self._request_post(RUTX11HTTPCommands.DHCP_STATIC_LEASES, data)
        if not success:
            click.secho("Failed to configure static leases.", fg="red")
            return

        print("Static leases configured successfully")

    def _request_get(self, command: str) -> tuple[bool, requests.Response]:
        url = self._request_url + command
        headers = {"Authorization": "Bearer " + self._token}

        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            click.secho(
                f"Failed to get data from {url}: {response.status_code} {response.reason}.",
                fg="red",
            )
            click.secho(f"Server response: {json.dumps(response.json(), indent=2)}")
            return False, response

        return True, response

    def _request_put(self, command: str, data: dict) -> tuple[bool, requests.Response]:
        url = self._request_url + command
        headers = {"Authorization": "Bearer " + self._token}

        response = requests.put(url, headers=headers, json=data, verify=False)
        if response.status_code != 200:
            click.secho(
                f"Failed to put data for {url}: {response.status_code} {response.reason}.",
                fg="red",
            )
            click.secho(f"Server response: {json.dumps(response.json(), indent=2)}")
            return False, response

        return True, response

    def _request_post(self, command: str, data: dict) -> tuple[bool, requests.Response]:
        url = self._request_url + command
        headers = {"Authorization": "Bearer " + self._token}

        response = requests.post(url, headers=headers, json=data, verify=False)
        if response.status_code != 200 and response.status_code != 201:
            click.secho(
                f"Failed to post data for {url}: {response.status_code} {response.reason}.",
                fg="red",
            )
            click.secho(f"Server response: {json.dumps(response.json(), indent=2)}")
            return False, response

        return True, response

    def _request_delete(self, command: str, data: dict) -> requests.Response:
        url = self._request_url + command
        headers = {"Authorization": "Bearer " + self._token}

        response = requests.delete(url, headers=headers, json=data, verify=False)
        if response.status_code != 200:
            click.secho(
                f"Failed to delete object for {url}: {response.status_code} {response.reason}.",
                fg="red",
            )
            click.secho(f"Server response: {json.dumps(response.json(), indent=2)}")
            return False, response

        return True, response


import argparse


def main(args=None):
    parser = argparse.ArgumentParser(description="RUTX11 Manager")
    parser.add_argument(
        "-i", "--device-ip", type=str, default="10.15.20.1", help="Device IP address"
    )
    parser.add_argument("--restore-default", action="store_true", help="Restore default settings")
    parsed_args = parser.parse_args(args)

    username = input("Enter the username: ")
    password = input("Enter the password: ")
    manager = RUTX11Manager(username=username, password=password, device_ip=parsed_args.device_ip)

    if parsed_args.restore_default:
        print("Restoring default settings")
        manager.factory_reset()
        manager.reboot()
        return


if __name__ == "__main__":
    main()
