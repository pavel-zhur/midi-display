1. https://www.raspberrypi.com/software/

2. https://zevs.by/monitory/lcd_3-5_320-480_r4
(wiki link given http://www.lcdwiki.com/3.5inch_RPi_Display?spm=a2g0o.detail.1000023.15.644f7c7f7Wg15M&file=3.5inch_RPi_Display)

```
sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
sudo ./LCD35-show
```

3. https://forums.raspberrypi.com/viewtopic.php?t=245810

& `dr_mode=peripheral`

4. https://forums.raspberrypi.com/viewtopic.php?t=347973

https://modclouddownloadprod.blob.core.windows.net/shared/mod-duo-rndis.zip

(downloaded here)

5.

```
sudo nano /etc/systemd/network/usb0.network
```

```
[Match]
Name=usb0

[Network]
Address=192.168.59.2/24
Gateway=192.168.59.1
DNS=192.168.59.1
```
Restart network service:
```
sudo systemctl restart systemd-networkd
```
Enable network service auto-start:
```
sudo systemctl enable systemd-networkd
```