# panther_rutx11

## Description

Network configuration scripts for RUTX11 router inside Panther or Lynx. Enables quick way to set WiFi client, WiFi access-point, cellular (LTE), GNSS, Husarnet network and more.
Scripts are compatible with Teltonika RUTX11 with firmware version ≥ `RUTX_R_00.07.02`.

## WiFi behavior

### Client Mode

Robot can be connected to the existing WiFi network on either 2.4GHz or 5GHz using it as an uplink. Multiple SSID can be set, the router will prioritize them in descending order.

### Access-point (STA mode)

In default configuration on both radios (2.4 GHz & 5 GHz) access-point is enabled with SSID `Panther_XXXX` / `Lynx_XXXX` and `Panther_5G_XXXX` / `Lynx_5G_XXXX`, where `XXXX` is serial number of the Robot. SSID, password, enabled radios can be changed via WebUI.

## Configuration

Configuration of the RUTX11 router can be performed using `rutx11_manager.py` script. When run the program will ask for `username` (default: *admin*) and `password` (default: *Husarion1*) of the router.

### Arguments

- **-i DEVICE_IP, --device-ip DEVICE_IP** (default: *10.15.20.1*): Device IP address
- **-c, --wifi-connect**: Connect to WiFi, program will ask for SSID and password of the network.
- **-d, --wifi-disconnect**: Disconnect from WiFi, the program will ask for SSID of the network to disconnect.
- **-s, --add-static-lease**: Add static lease, the program will ask for IP, MAC address and name of the lease.
- **--restore-default**: Restore default settings of the router, the program will ask for robot model (PTH/LNX) and robot serial number.
### Example usage

#### Connect to WiFi

```bash
./rutx11_manager.py -c
```

#### Restore Default Configuration

```bash
./rutx11_manager.py --restore-default
```
