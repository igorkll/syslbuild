#!/bin/bash

useradd -d /home/user -s /bin/bash user
echo 'user:user' | chpasswd

echo test > /home/user/test.txt
