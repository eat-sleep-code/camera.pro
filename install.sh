# This script will install the camera and any required prerequisites.
cd ~
echo -e ''
echo -e '\033[32mCamera PRO [Installation Script] \033[0m'
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e ''
echo -e '\033[93mUpdating package repositories... \033[0m'
sudo apt update


echo ''
echo -e '\033[93mInstalling prerequisites... \033[0m'
sudo apt install -y git python3 python3-pip python3-picamera2 python3-evdev ffmpeg libopenblas-dev daemontools daemontools-run wget
sudo python3 -m venv --system-site-packages ~/camera.pro-venv
sudo ~/camera.pro-venv/bin/pip3 install piexif ffmpeg-python moviepy pyside6 qtawesome

echo ''
echo -e '\033[93mInstalling YouTube upload prerequisites (optional)... \033[0m'
sudo ~/camera.pro-venv/bin/pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib \
  || echo -e '\033[93mWarning: YouTube upload prerequisites could not be installed. Core camera features are unaffected.\033[0m'


echo ''
echo -e '\033[93mProvisioning logs... \033[0m'
sudo mkdir -p /home/pi/logs
sudo chmod +rw /home/pi/logs
sudo sed -i '\|^tmpfs /home/pi/logs|d' /etc/fstab
sudo sed -i '$ a tmpfs /home/pi/logs tmpfs defaults,noatime,nosuid,size=16m 0 0' /etc/fstab
sudo systemctl daemon-reload
sudo mount -a


echo ''
echo -e '\033[93mInstalling Camera... \033[0m'
cd ~
sudo mv ~/camera.pro/config.json ~/camera-config.json.bak 2> /dev/null || true
sudo mv ~/camera.pro/youtube/config.json ~/camera-youtube-config.json.bak 2> /dev/null || true
sudo mv ~/camera.pro/youtube/token.json ~/camera-youtube-token.json.bak 2> /dev/null || true
sudo rm -Rf ~/camera.pro
sudo git clone https://github.com/eat-sleep-code/camera.pro
sudo chown -R $USER:$USER camera.pro
cd camera.pro
sudo chmod +x camera.py
sudo chmod +x ~/camera.pro/youtube/upload.py
sudo chmod +x ~/camera.pro/youtube/echo.py
sudo mkdir -p ~/dcim
sudo chown -R $USER:$USER ~/dcim
sudo chown -R $USER:$USER ~/logs




echo ''
echo -e '\033[93mSetting up autostart service... \033[0m'
cd ~
echo 'Removing legacy daemontools service instance (if present)...'
sudo svc -d /etc/service/camera.pro 2>/dev/null || true
sudo rm -Rf /etc/service/camera.pro
echo 'Installing systemd service...'
sudo cp ~/camera.pro/camera.service /etc/systemd/system/
sudo systemctl daemon-reload
echo 'Please see the README file for more information on enabling autostart.'


cd ~
echo ''
echo -e '\033[93mSetting up aliases... \033[0m'
sudo touch ~/.bash_aliases
sudo sed -i '/\b\(function camera\)\b/d' ~/.bash_aliases
sudo sed -i '/\b\(camera-enable\|camera-disable\|camera-status\|touch-enable\|touch-disable\|touch-status\)\b/d' ~/.bash_aliases
sudo sed -i '$ a function camera { sudo ~/camera.pro-venv/bin/python3 ~/camera.pro/camera.py "$@"; }' ~/.bash_aliases
sudo sed -i '$ a alias camera-enable="sudo systemctl enable camera && sudo systemctl start camera"' ~/.bash_aliases
sudo sed -i '$ a alias camera-disable="sudo systemctl disable camera && sudo systemctl stop camera"' ~/.bash_aliases
sudo sed -i '$ a alias camera-status="sudo systemctl status camera && sudo journalctl -u camera -f"' ~/.bash_aliases
sudo sed -i '$ a alias touch-enable="sudo systemctl enable ft5506-touch && sudo systemctl start ft5506-touch"' ~/.bash_aliases
sudo sed -i '$ a alias touch-disable="sudo systemctl disable ft5506-touch && sudo systemctl stop ft5506-touch"' ~/.bash_aliases
sudo sed -i '$ a alias touch-status="sudo systemctl status ft5506-touch && sudo journalctl -u ft5506-touch -f"' ~/.bash_aliases
echo -e 'You may use \e[1mcamera\e[0m to launch the program manually.'
echo -e 'You may use \e[1mcamera-enable\e[0m / \e[1mcamera-disable\e[0m / \e[1mcamera-status\e[0m to manage the camera service.'
echo -e 'You may use \e[1mtouch-enable\e[0m / \e[1mtouch-disable\e[0m / \e[1mtouch-status\e[0m to manage the FT5506 touch driver.'
echo ''
echo 'To use the automatic YouTube upload feature, you will need to update the youtube/config.json.'
echo 'Please see the README file for more information.'
echo ''
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e '\033[32mInstallation completed. \033[0m'
echo ''
#sudo rm ~/install-camera.sh
bash
