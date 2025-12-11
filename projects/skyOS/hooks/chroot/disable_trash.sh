# disable getty
systemctl mask getty.target

# disable auto quit plymouth
systemctl mask plymouth-quit.service
