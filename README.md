# panther_rutx11
## Description
Network configuration scripts for RUTX11 router inside Panther. Enables quick way to set WiFi client, WiFi access-point, cellular (LTE), GNSS, Husarnet network and more.
Scripts are compatible with Teltonika RUTX11 with firmware version ≥ `RUTX_R_00.07.02`.
## WiFi behavior

### Client Mode 

Panther can be connected to the existing WiFi network on either 2.4GHz or 5GHz using it as an uplink. Multiple SSID can be set, the router will prioritize them in descending order.

### Access-point (STA mode)

In default configuration on both radios (2.4 GHz & 5 GHz) access-point is enabled with SSID `Panther_XXXX` and `Panther_5G_XXXX`, where `XXXX` is serial number of Panther. SSID, password, enabled radios can be changed via WebUI.

## Configuration

Configuration is stored in `config.json` file using extended version of JSON, which enables comments and advanced error messages.
To apply new configuration, execute `setup_wifi.py` which is located in the same folder as `config.json` by command: `./setup_wifi.py`.

## Configuration options

Config file is divided into sections (arrays), which are listed with possible options as below.
| Section name      | Multiple arrays |
|-------------------|-----------------|
| wifi_client_radio | no              |
| wifi_client       | yes             |
| cellular          | yes             |
| gnss              | no              |
| husarnet          | no              |

### wifi_client_radio
Set radio to use with Client Mode.
| Option            | Required | Default value | Description / valid values                                           |
|-------------------|----------|---------------|----------------------------------------------------------------------|
| wifi_client_radio | no       | 0             | 0 - 2.4GHz radio used for up-link<br>1 - 5GHz radio used for up-link |

### wifi_client

This section can contain multiple arrays of below option:
| Option   | Required | Default value | Description / valid values                                                                                                  |
|----------|----------|---------------|-----------------------------------------------------------------------------------------------------------------------------|
| ssid     | yes      | -             | SSID (name) of WiFi network to join.                                                                                        |
| password | no       | -             | Password protecting chosen network.<br>For `open` encryption not required.<br>For `psk2` length is minimum of 8 characters. |

### Husarnet

|   Option  | Required | Default value |                    Description / valid values                    |
|:---------:|:--------:|:-------------:|:----------------------------------------------------------------:|
|  hostname |    yes   |       -       |   Desired hostname in your Husarnet network. Should be unique.   |
| join_code |    yes   |       -       | Join code to your Husarnet network. More info how to obtain it is available [here](https://husarnet.com/docs/manual-dashboard#join-code-tab)  |

## Example config files 
### Example 1 - single WiFi client on 2.4GHz and connecting to Husarnet
    {
        "husarnet":{
            "hostname":"your_desired_hostname",
            "join_code":"your_join_code"
        },
        "wifi_client_radio":0,
        "wifi_client":[

            {
                "radio":"0",
                "ssid":"SSID_of_your_network",
                "password":"password_to_your_network",

            }

        ]
    }

### Example 2 - two WiFi clients on 5GHz and using different GNSS constellations 

    {
        "wifi_client_radio":1,
        "wifi_client":[

            {
                "ssid":"SSID_of_your_network",
                "password":"password_to_your_network"
            },
            {
                "ssid":"SSID_of_your_second_network",
                "password":"password_to_your_second_network",
            }


        ]

    }