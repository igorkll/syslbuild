echo "root:root" | chpasswd
usermod -s /bin/bash root

useradd -s /usr/sbin/nologin mp3player

systemctl mask getty@tty2.service
systemctl mask getty@tty3.service
systemctl mask getty@tty4.service
systemctl mask getty@tty5.service
systemctl mask getty@tty6.service

systemctl enable mp3player
systemctl enable dbus

loginctl enable-linger mp3player

update-initramfs -u