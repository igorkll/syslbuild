#!/bin/bash

useradd -m -d /home/user -s /bin/bash user
echo 'user:user' | chpasswd

echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user-nopasswd
chmod 440 /etc/sudoers.d/user-nopasswd

chown -R user:user /home/user
#chmod 700 /home/user

echo test > /home/user/test.txt
