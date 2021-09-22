# panther_rutx11
## Description
Network configuration scripts for RUTX11 router inside Panther. Enables quick way to set WiFi client, WiFi access-point, cellular (LTE), GNSS, Husarnet network and more.
Scripts are compatible with Teltonika RUX11 running customized OpenWRT-19.XX with latest [Travelmate](https://github.com/openwrt/packages/tree/openwrt-19.07/net/travelmate/files) package installed. 

## WiFi behavior

### Client Mode 

Panther can be connected to existing WiFi network on 2.4 GHz using it as an uplink. Multiple SSID can be set, router will prioritize them in descending order. If signal strength falls below set limit next (if available) network will be used. 

**Note:** While uplink on 5 GHz radio is possible, due to chipset limitations it is impossible to enable roaming and multiple SSID. As a result we recommend using 2.4 GHZ for uplink.

### Access-point (STA mode)

In default configuration on both radios (2.4 GHz & 5 GHz) access-point is enabled with SSID `Panther_XXXX` and `Panther_5G_XXXX`, where `XXXX` is serial number of Panther. SSID, password, enabled radios can be changed (see configuration options below)

## Configuration

Configuration is stored in `config.json` file using extended version of JSON, which enables comments and advanced error messages.
To apply new configuration execute `setup.py` which is located in the same folder as `config.json` by command: `./setup.py`.

## Configuration options

Config file is divided into sections (arrays), which are listed with possible options as bellow.
| Section name | Multiple arrays |
|:------------:|:---------------:|
|  wifi_client |       yes       |
|    wifi_ap   |        no       |
|   cellular   |       yes       |
|     gnss     |        no       |
|   husarnet   |        no       |

### wifi_client

This section can contains multiple arrays of below option:
|   Option   | Required | Default value |                                                 Description / valid values                                                 |
|:----------:|:--------:|:-------------:|:--------------------------------------------------------------------------------------------------------------------------:|
|    radio   |    yes   |       -       |                       Defines used radio. `0` is recommended.<br>`0` - 2.4 GHz radio<br>`1` - 5 GHz radio                       |
|    ssid    |    yes   |       -       |                                            SSID (name) of WiFi network to join.                                            |
| encryption |    yes   |       -       |                 `open` - open network<br>`psk2` - WPA2 encrypted network<br>WEP encryption is not supported.                |
|  password  |    no    |       -       | Password protecting chosen network.<br>For `open` encryption not required.<br>For `psk2` length is minimum of 8 characters. |

### wifi_ap

This section is used to configure access-point setting. Most common use is changing default password for WiFi. Can contains multiple arrays of below option
|   Option   | Required |                               Default value                               |                                                 Description / valid values                                                 |
|:----------:|:--------:|:-------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------:|
|    radio   |    yes   |                                     -                                     |                               Defines used radio.<br>`0` - 2.4 GHz radio<br>`1` - 5 GHz radio                              |
|    ssid    |    no    | Panther_XXXX for 2.4 GHz (radio 0)<br>Panther_5G_XXXX for 5 GHz (radio 1) |                SSID (name) of WiFi network to create. <br>`XXXX` in default value is Panther serial number.                |
| encryption |    yes   |                                     -                                     |                 `open` - open network<br>`psk2` - WPA2 encrypted network<br>WEP encryption is not supported.                |
|  password  |    no    |                                     -                                     | Password protecting chosen network.<br>For `open` encryption not required.<br>For `psk2` length is minimum of 8 characters. |

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
### Example 1 - single WiFi client and connecting to Husarnet
    {
        "husarnet":{
            "hostname":"your_desired_hostname",
            "join_code":"your_join_code"
        },
        "wifi_client":[

            {
                "radio":"0",
                "ssid":"SSID_of_your_network",
                "password":"password_to_your_network",
                "encryption":"psk2"
            }

        ]
    }

### Example 2 - two WiFi clients and using different GNSS constellations 

    {
        
        "wifi_client":[

            {
                "radio":"0",
                "ssid":"SSID_of_your_network",
                "password":"password_to_your_network",
                "encryption":"psk2"
            },
            {
                "radio":"0",
                "ssid":"SSID_of_your_second_network",
                "password":"password_to_your_second_network",
                "encryption":"psk2"
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