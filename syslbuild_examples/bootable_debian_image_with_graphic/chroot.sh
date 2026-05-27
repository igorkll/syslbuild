#!/bin/bash

useradd -d /home/user -s /bin/bash user
usermod -aG sudo user
echo 'user:user' | chpasswd

chown -R user:user /home/user
chmod 700 /home/user

plymouth-set-default-theme -R spinner

echo test > /home/user/test.txt
