# Camera PRO

> [!WARNING]
 This software is a fully functional beta and is still undergoing testing. Please report any issues you encounter.

---

## Getting Started

- Use [Raspberry Pi Imager](https://www.raspberrypi.com/software) to install Raspberry Pi OS *(Trixie)* on a microSD card
- Use [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md) to verify that:
  - CSI camera interface is enabled
  - WiFi connection is configured
- Execute the following to update all installed software to the latest version(s):
```bash
sudo apt update && sudo apt full-upgrade -y && sudo apt autoremove -y && sudo apt autoclean
```
- Connect the Raspberry Pi camera(s) to your Raspberry Pi


## Installation

Installation of the program, as well as any software prerequisites, can be completed with the following two-line install script.

```bash
wget -q https://raw.githubusercontent.com/eat-sleep-code/camera.pro/master/install.sh -O ~/install.sh
sudo chmod +x ~/install.sh && ~/install.sh
```

---

## Usage
```bash
camera
```

---

## Autostart

Camera PRO runs as root (required for framebuffer and camera hardware access) via a systemd service.  The install script sets up the service and adds the following shell aliases for convenience:

### Commands
| Alias | Action |
|---|---|
| `camera-enable` | Enable autostart on boot and start immediately |
| `camera-disable` | Disable autostart and stop immediately |
| `camera-status` | Show service status and tail the live log |
| `camera-update` | Download and run the latest install script |

> [!NOTE]
> Reload your shell after installation (`bash` or open a new terminal) for the aliases to become available.


### Manual Installation

```bash
sudo cp ~/camera.pro/camera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera
sudo systemctl start camera
```

---

## Legacy Display Touch Support

We encountered issues getting touch to work with a legacy Waveshare display in combination with Raspberry Pi OS Lite (Trixie).   This display featured the FT5506 touch panel controller.   To address this, we developed a custom driver.   If you are working with one of these older displays, you will need to enable this custom driver.

### Commands

| Alias | Action |
|---|---|
| `touch-enable` | Enable the FT5506 touch driver on boot and start immediately |
| `touch-disable` | Disable the FT5506 touch driver and stop immediately |
| `touch-status` | Show touch driver status and tail the live log |


### Manual Installation
```bash
# 1. Copy the service file and install it
sudo cp ~/camera.pro/ft5506-touch.service /etc/systemd/system/
sudo systemctl daemon-reload

# 2. Rebuild and reinstall the DT overlay (disables kernel driver)
dtc -@ -I dts -O dtb -o /tmp/ft5506-poll.dtbo /tmp/ft5506-poll.dts
sudo cp /tmp/ft5506-poll.dtbo /boot/firmware/overlays/ft5506-poll.dtbo

# 3. Enable the touch driver and reboot
touch-enable
sudo reboot
```

> [!NOTE]
> On some displays, systemd may log a recurring error for a service such as `systemd-backlight@backlight:10-0045.service` because it cannot read or write the display's backlight interface.  This is harmless but noisy.  If you see this, identify the exact service name with `sudo systemctl --failed` and mask it:
> ```bash
> sudo systemctl mask systemd-backlight@backlight:<device>.service
> ```
---

## Infrared Cameras
If you are using an infrared (IR) camera, you may need to modify the Auto White Balance (AWB) mode at boot time.

This can be achieved by executing `sudo nano /boot/config.txt` and adding the following lines.

```bash
# Camera Settings 
awb_auto_is_greyworld=1
```

> [!NOTE]
> While IR cameras utilize "invisible" (outside the spectrum of the human eye) light, they can not magically see in the dark.   You will need to illuminate night scenes with one or more IR lights to take advantage of an Infrared Camera.

---

## Automatic YouTube Upload

- Copy [youtube/config.json.example](config.json.example) to a new file called __youtube/config.json__.
- Sign in to the [Google APIs & Services](https://console.cloud.google.com/apis/dashboard) console.
- If necessary, create a new Project.
- Expand the left menu and select the __Enabled APIs & services__ menu item.
- Click the __+ ENABLE APIS AND SERVICES__ button.
- Search for &ndash; and enable &ndash; the __YouTube Data API v3__.
- Select the __Credentials__ menu item from the left menu.
- Click the __+ CREATE CREDENTIALS__ button and select __OAuth client ID__ from the dropdown menu that appears.
- :heavy_exclamation_mark: Select __Desktop app__ from the __Application Type__ dropdown menu.  Selecting any other option from the list will make authentication impossible. :heavy_exclamation_mark:
- Enter an appropriate value in the __Name__ field and click the Submit button.   
- From the screen that appears, copy the Client ID and Client Secret and paste them in the appropriate places within the config.json file you created in the first step.
- Open a terminal and execute `./camera/youtube/authorize.sh`.  You will be prompted to open a link in the browser.
- You will receive a warning about only continuing if you trust the requestor.   If you trust yourself, advance to the final step to complete the authentication process.

---

> [!TIP]
> You may wish to increase your SWAP file to match your memory size as outlined in this [third-party guide](https://pimylifeup.com/raspberry-pi-swap-file/).

---

