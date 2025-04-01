#!/usr/bin/env python3

import argparse
import click
import getpass
import json
import requests
import subprocess
import time
import urllib3


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
    WIRELESS_MULTI_AP = "/api/wireless/multi_ap/config"
    GPS_GLOBAL = "/api/gps/global"
    GPS_NMEA_NMEA_FORWARDING = "/api/gps/nmea/config/nmea_forwarding"
    GPS_NMEA_RULES = "/api/gps/nmea/rules/config"
    NTP_NTP_CLIENT = "/api/date_time/ntp/client/config/ntpclient"
    RMS_ACTIONS_CONNECT = "/api/rms/actions/connect"
    FIREWALL_ZONES_ID3 = "/api/firewall/zones/config/3"


class RUTX11Manager:
    def __init__(self, username: str, password: str, device_ip: str = "10.15.20.1") -> None:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._username = username
        self._password = password
        self._token = None
        self._device_ip = device_ip
        self._request_url = "https://" + device_ip

        if not self._is_available():
            raise Exception(f"Device at {device_ip} is not available")

        self._login()

    def factory_reset(self, robot_model: str, robot_serial_number: str) -> None:
        if robot_model not in ["PTH", "LNX"]:
            raise Exception("Invalid robot model. Valid options are 'PTH' or 'LNX'.")

        if len(robot_serial_number) != 4:
            raise Exception("Robot serial number must be 4 characters long")

        self._robot_model = robot_model
        self._robot_serial_number = robot_serial_number

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

    def add_wifi_network(self, ssid: str, password: str) -> None:
        success, response = self._request_get(RUTX11HTTPCommands.WIRELESS_MULTI_AP)
        if not success:
            raise Exception("Failed to get WiFi networks")

        data = {
            "data": {
                "enabled": "1",
                "ssid": ssid,
                "key": password,
            }
        }

        for network in response.json()["data"]:
            if network["ssid"] == ssid:
                click.secho("WiFi network already exists, updating password", fg="yellow")
                success, _ = self._request_put(
                    f"{RUTX11HTTPCommands.WIRELESS_MULTI_AP}/{network['id']}", data
                )

                if not success:
                    raise Exception("Failed to update WiFi network")

                print("WiFi network updated successfully")
                return

        success, _ = self._request_post(RUTX11HTTPCommands.WIRELESS_MULTI_AP, data)
        if not success:
            raise Exception("Failed to add WiFi network")

        print("WiFi network added successfully")

    def remove_wifi_network(self, ssid: str) -> None:
        success, response = self._request_get(RUTX11HTTPCommands.WIRELESS_MULTI_AP)
        if not success:
            raise Exception("Failed to get WiFi networks", fg="red")

        for network in response.json()["data"]:
            if network["ssid"] == ssid:
                success, _ = self._request_delete(
                    f"{RUTX11HTTPCommands.WIRELESS_MULTI_AP}/{network['id']}", {}
                )

                if not success:
                    raise Exception("Failed to remove WiFi network", fg="red")

                print("WiFi network removed successfully")
                return

        click.secho("WiFi network not found", fg="yellow")

    def add_static_lease(self, ip: str, mac: str, name: str) -> None:
        if ip == "" or mac == "" or name == "":
            raise Exception("IP, MAC and name are required", fg="red")

        ip_parts = ip.split(".")
        if len(ip_parts) != 4:
            raise Exception("Invalid IP address", fg="red")

        mac_parts = mac.split(":")
        if len(mac_parts) != 6:
            raise Exception("Invalid MAC address", fg="red")

        data = {
            "data": {
                "ip": ip,
                "mac": mac,
                "name": name,
            }
        }

        success, _ = self._request_post(RUTX11HTTPCommands.DHCP_STATIC_LEASES, data)
        if not success:
            raise Exception("Failed to add static lease.", fg="red")

        print("Static lease added successfully")

    def check_internet_connection(self) -> bool:
        return self._ping_ip("8.8.8.8")

    def _is_available(self) -> bool:
        return self._ping_ip(self._device_ip)

    def _ping_ip(self, ip: str) -> bool:
        try:
            res = subprocess.run(
                ["ping", "-c 1", "-w 1", ip],
                capture_output=True,
                text=True,
                check=True,
            )
            if res.returncode != 0:
                return False
        except subprocess.CalledProcessError:
            return False

        return True

    def _login(self) -> None:
        url = self._request_url + RUTX11HTTPCommands.LOGIN
        data = {
            "username": self._username,
            "password": self._password,
        }

        response = requests.post(url, json=data, verify=False)
        if response.status_code != 200:
            click.secho(f"Failed to connect: {json.dumps(response.json(), indent=2)}", fg="red")
            raise Exception(f"Failed to connect")

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
        prefix = "Lynx_" if self._robot_model == "LNX" else "Panther_"

        data = {
            "data": [
                {
                    "id": "default_radio0",
                    "ssid": prefix + self._robot_serial_number,
                    "key": "husarion",
                },
                {
                    "id": "default_radio1",
                    "ssid": prefix + "5G_" + self._robot_serial_number,
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

        if response.json()["data"]:
            data_delete = {"data": [lease["id"] for lease in response.json()["data"]]}
            success, _ = self._request_delete(RUTX11HTTPCommands.DHCP_STATIC_LEASES, data_delete)
            if not success:
                click.secho("Failed to delete static leases.", fg="red")
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


def main(args=None):
    parser = argparse.ArgumentParser(description="RUTX11 Manager")
    parser.add_argument(
        "-i", "--device-ip", type=str, default="10.15.20.1", help="Device IP address"
    )
    parser.add_argument("-c", "--wifi-connect", action="store_true", help="Connect to WiFi")
    parser.add_argument("-d", "--wifi-disconnect", action="store_true", help="Disconnect from WiFi")
    parser.add_argument("-s", "--add-static-lease", action="store_true", help="Add static lease")
    parser.add_argument("--restore-default", action="store_true", help="Restore default settings")
    parsed_args = parser.parse_args(args)

    try:
        username = input("Enter the username: ")
        password = getpass.getpass("Enter the password: ")
        manager = RUTX11Manager(
            username=username, password=password, device_ip=parsed_args.device_ip
        )
    except Exception as err:
        click.secho(f"Failed to create RUTX11Manager: {err}", fg="red")
        return

    if parsed_args.restore_default:
        print("Restoring default settings")
        robot_model = input("Enter the robot model (PTH/LNX): ")
        robot_serial_number = input("Enter the robot serial number: ")
        manager.factory_reset(robot_model, robot_serial_number)
        manager.reboot()
        return

    if parsed_args.wifi_disconnect:
        print("Disconnecting from WiFi")
        ssid = input("Enter the WiFi SSID: ")
        try:
            manager.remove_wifi_network(ssid)
        except Exception as err:
            click.secho(f"Failure: {err}", fg="red")

    if parsed_args.wifi_connect:
        print("Connecting to WiFi")
        ssid = input("Enter the WiFi SSID: ")
        password = getpass.getpass("Enter the password: ")

        try:
            manager.add_wifi_network(ssid, password)
        except Exception as err:
            click.secho(f"Failure: {err}", fg="red")
            return

        start_time = time.time()
        timeout = 180  # 3 minutes
        print("Waiting to establish an internet connection. This may take few minutes.")
        while not manager.check_internet_connection():
            time_diff = time.time() - start_time
            if time_diff > timeout:
                click.secho(
                    "\nFailed to connect to the internet. Check SSID name and password", fg="red"
                )
                return

            dots = "." * int(time_diff % 3 + 1)
            print(f"\r{' ' * 4}\r{dots}", end="", flush=True)

        print("\nConnected to the Internet")

    if parsed_args.add_static_lease:
        ip = input("Enter the IP address: ")
        mac = input("Enter the MAC address: ")
        name = input("Enter the name: ")
        try:
            manager.add_static_lease(ip, mac, name)
        except Exception as err:
            click.secho(f"Failure: {err}", fg="red")


if __name__ == "__main__":
    main()
