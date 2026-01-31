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
