# set root password (for debug)
echo "root:root" | chpasswd
usermod -s /bin/bash root

# system lockdown
systemctl mask getty@tty2.service
systemctl mask getty@tty3.service
systemctl mask getty@tty4.service
systemctl mask getty@tty5.service
systemctl mask getty@tty6.service

# create mp3player user
useradd -m -s /usr/sbin/nologin mp3player
systemctl enable mp3player
systemctl enable dbus
loginctl enable-linger mp3player

# update init ram disk
update-initramfs -u