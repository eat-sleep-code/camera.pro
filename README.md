# Camera PRO

> [!WARNING]
This is not yet a working application.   Once complete, it will replace the current [Camera](https://github.com/eat-sleep-code/camera) program.

The below information is incomplete / inaccurate at this time.

---

## Getting Started

- Use [Raspberry Pi Imager](https://www.raspberrypi.com/software) to install Raspberry Pi OS *(Bookworm)* on a microSD card
- Use [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md) to:
  - Enable the CSI camera interface
  - Set up your WiFi connection
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

## Autostart

### Enable

To enable autostart of the program, execute the following command:

```
sudo mv /etc/service/camera.pro/run.disabled /etc/service/camera.pro/run
```

### Disable

To disable autostart of the program, execute the following command:

```
sudo mv /etc/service/camera.pro/run /etc/service/camera.pro/run.disabled
```

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

> [!TIP]
> You may wish to increase your SWAP file to match your memory size as outlined in this [third-party guide](https://pimylifeup.com/raspberry-pi-swap-file/).

---

