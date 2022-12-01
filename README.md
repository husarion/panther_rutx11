# panther_rutx11
## Description
Network configuration scripts for RUTX11 router inside Panther. Enables quick way to set WiFi client, WiFi access-point, cellular (LTE), GNSS, Husarnet network and more.
Scripts are compatible with Teltonika RUTX11 with firmware version ≥ `RUTX_R_00.07.02.7`.
## WiFi behavior

### Client Mode 

Panther can be connected to the existing WiFi network on either 2.4GHz or 5GHz using it as an uplink. Multiple SSID can be set, the router will prioritize them in descending order.

### Access-point (STA mode)

In default configuration on both radios (2.4 GHz & 5 GHz) access-point is enabled with SSID `Panther_XXXX` and `Panther_5G_XXXX`, where `XXXX` is serial number of Panther. SSID, password, enabled radios can be changed via WebUI.

## Configuration

Configuration is stored in `config.json` file using extended version of JSON, which enables comments and advanced error messages.
To apply new configuration, execute `setup.py` which is located in the same folder as `config.json` by command: `./setup.py`.

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
### cellular

|     Option     | Required | Default value |                                                                                                                         Description / valid values                                                                                                                         |
|:--------------:|:--------:|:-------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|       sim      |    yes   |       -       |                                                                                                   Defines used SIM slot.<br>`0` - first SIM slot<br>`1` - second SIM slot                                                                                                  |
|     enable     |    yes   |       -       |                                                                                                               `0` - disable SIM slot<br>`1` - enable SIM slot                                                                                                              |
|       pin      |    no    |       -       |                                                                    PIN code to SIM card. 4 to 8 digits in length. <br>Please remember, that SIM card will lock after 3 attempts with incorrect PIN code!                                                                   |
|       apn      |    no    |       -       |                                                  Fill if custom APN name is required by your operator (to get public IP for example).<br>If left empty Android APN database will be used to find proper to your operator.                                                  |
| authentication |    no    |      none     | `none` - chose if no additional authentication scheme is required by your operator.<br>`pap` - PAP authentication scheme will be used. Username and password must be filled in.<br>`chap` - CHAP authentication scheme will be used. Username and password must be fill in. |
|    username    |    no    |       -       |                                                                                                                  Username for PAP or CHAP authentication.                                                                                                                  |
|    password    |    no    |       -       |                                                                                                         Password matching username for PAP or CHAP authentication.                                                                                                         |
### gnns

|  Option  | Required | Default value |                                       Description / valid values                                      |
|:--------:|:--------:|:-------------:|:-----------------------------------------------------------------------------------------------------:|
|  enable  |    no    |       1       |                                  0 - disable GNSS<br>1 - enable GNSS                                  |
|    gps   |    no    |       1       |          Controls usage of GPS satellite constellation.<br>0 - disable GPS<br>1 - enable GPS          |
|  glonass |    no    |       1       |    Controls usage of GLONASS satellite constellation.<br>0 - disable GLONASS<br>1 - enable GLONASS    |
|   beidu  |    no    |       0       |       Controls usage of BEIDU satellite constellation.<br>0 - disable BEIDU<br>1 - enable BeiDu       |
|  galileo |    no    |       0       |    Controls usage of Galileo satellite constellation.<br>0 - disable Galileo<br>1 - enable Galileo    |
|    ip    |    no    |   10.15.20.2  |                          IP address where navigational messages are forwarded                         |
|   port   |    no    |      5000     |                             Port where navigational messages are forwarded                            |
| protocol |    no    |      udp      |                 Network protocol used to forward navigational messages.<br>udp<br>tcp                 |
| interval |    no    |       1       | Interval in seconds how often send navigational messages to specified host.<br>Valid values: 1 to 60. |

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


        ],

        "gnss":{
            "galileo":"1",
            "glosnass":"0"
        }

    }
### Example 3 - using cellular network with dual SIM, SIM 1 with custom APN and CHAP authorization, SIM 2 with pin setting. Changing password of access point
    
    {
        
        "cellular":[

            {
                "sim":"0",
                "enable":"1",
                "apn":"custom_apn",
                "authentication":"chap",
                "username":"your_username",
                "password":"your_password"
            },
            {
                "sim":"1",
                "enable":"1",
                "pin":"0000"
            }


        ],

        "wifi_ap":{
            "encryption":"psk2",
            "password":"new_password"
        }

    }