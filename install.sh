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
sudo apt install -y git python3 python3-pip python3-picamera2 ffmpeg libopenblas-dev
sudo python3 -m venv ~/camera-venv
sudo ~/camera-venv/bin/pip3 install piexif ffmpeg-python google-api-python-client google-auth-httplib2 google-auth-oauthlib oauth2client moviepy pyside6 evdev


echo ''
echo -e '\033[93mProvisioning logs... \033[0m'
sudo mkdir -p /home/pi/logs
sudo chmod +rw /home/pi/logs
sudo sed -i '\|^tmpfs /home/pi/logs|d' /etc/fstab
sudo sed -i '$ a tmpfs /home/pi/logs tmpfs defaults,noatime,nosuid,size=16m 0 0' /etc/fstab
sudo mount -a


echo ''
echo -e '\033[93mInstalling Camera... \033[0m'
cd ~
sudo mv ~/camera/config.json ~/camera-config.json.bak 2> /dev/null || true
sudo mv ~/camera/youtube/config.json ~/camera-youtube-config.json.bak 2> /dev/null || true
sudo mv ~/camera/youtube/token.json ~/camera-youtube-token.json.bak 2> /dev/null || true
sudo rm -Rf ~/camera
sudo git clone https://github.com/eat-sleep-code/camera.pro
sudo chown -R $USER:$USER camera
cd camera
sudo chmod +x camera.py
sudo chmod +x ~/camera/youtube/upload.py
sudo chmod +x ~/camera/youtube/echo.py
sudo mkdir -p ~/dcim
sudo chown -R $USER:$USER ~/dcim
sudo chown -R $USER:$USER ~/logs


echo ''
echo -e '\033[093mSetting up autostart daemon... \033[0m'
cd ~
sudo svc -d /etc/service/camera.pro
sudo rm -Rf /etc/service/camera.pro
sudo mkdir /etc/service/camera.pro
sudo mv ~/camera.zero/run.disabled /etc/service/camera.pro/run.disabled
sudo chmod +x /etc/service/camera.pro/run.disabled
sudo chown -R root:root /etc/service/camera.pro
echo 'Please see the README file for more information on configuring autostart.'


cd ~
echo ''
echo -e '\033[93mSetting up aliases... \033[0m'
sudo touch ~/.bash_aliases
sudo sed -i '/\b\(function camera\)\b/d' ~/.bash_aliases
sudo sed -i '$ a function camera { sudo ~/camera-venv/bin/python3 ~/camera/camera.py "$@"; }' ~/.bash_aliases
echo -e 'You may use \e[1mcamera <options>\e[0m to launch the program.'
echo ''
echo 'To use the automatic YouTube upload feature, you will need to update the youtube/config.json.'
echo 'Please see the README file for more information.'
echo ''
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e '\033[32mInstallation completed. \033[0m'
echo ''
#sudo rm ~/install-camera.sh
bash
