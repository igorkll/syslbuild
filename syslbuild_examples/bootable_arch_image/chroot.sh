#!/bin/bash

# ------------ create user
mkdir -p /home/user
useradd -d /home/user -s /bin/bash user
echo 'user:user' | chpasswd
cp -an /etc/skel/. /home/user
chown -R user:user /home/user
chmod 700 /home/user

# ------------ setup sudo
echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user-nopasswd
chmod 440 /etc/sudoers.d/user-nopasswd

# ------------ example
echo test > /home/user/test.txt
