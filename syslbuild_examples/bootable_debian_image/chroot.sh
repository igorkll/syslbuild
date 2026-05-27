#!/bin/bash

useradd -d /home/user -s /bin/bash user
usermod -aG sudo user

echo 'user:user' | chpasswd

echo test > /home/user/test.txt
