echo "root:root" | chpasswd
usermod -s /bin/bash root

useradd -s /usr/sbin/nologin mp3player

systemctl enable mp3player
systemctl enable dbus

loginctl enable-linger mp3player

update-initramfs -u