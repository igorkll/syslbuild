# remove documentation
rm -rf /usr/share/man
rm -rf /usr/share/doc
rm -rf /usr/share/info

# remove package manager
rm -f /usr/bin/apt*
rm -f /usr/bin/dpkg*
rm -rf /usr/lib/apt
rm -rf /usr/lib/dpkg
rm -rf /usr/share/dpkg
rm -rf /var/lib/apt
rm -rf /var/lib/dpkg
rm -rf /etc/apt
rm -rf /etc/dpkg

# remove systemd
rm -f /usr/bin/systemctl
rm -f /usr/bin/systemd*
rm -rf /usr/share/systemd
rm -rf /usr/lib/systemd
rm -rf /var/lib/systemd
rm -rf /etc/systemd

# remove user system
rm -f /etc/shadow
rm -f /etc/gshadow
rm -f /etc/passwd
rm -f /etc/group
rm -f /etc/shadow-
rm -f /etc/gshadow-
rm -f /etc/passwd-
rm -f /etc/group-
rm -f /usr/sbin/getty
rm -f /usr/sbin/agetty
rm -f /usr/sbin/adduser
rm -f /usr/sbin/addgroup
rm -f /usr/sbin/deluser
rm -f /usr/sbin/delgroup
rm -f /usr/sbin/useradd
rm -f /usr/sbin/usermod
rm -f /usr/sbin/userdel
rm -f /usr/sbin/pwck
rm -f /usr/sbin/pwconv
rm -f /etc/login.defs
rm -f /etc/default/useradd
rm -rf /etc/skel
