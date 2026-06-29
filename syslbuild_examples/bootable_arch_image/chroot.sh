#!/bin/bash

useradd -d /home/user -s /bin/bash user
usermod -aG wheel user
echo 'user:user' | chpasswd

chown -R user:user /home/user
chmod 700 /home/user

echo test > /home/user/test.txt
