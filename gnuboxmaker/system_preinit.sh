#!/bin/sh

data_link() {
	if [ ! -d "/root/data/$1" ]; then
        cp -a "/root/$1" "/root/data/$1"
    fi

    /nativemount --bind "/root/data/$1" "/root/$1"
}

for x in $(cat /proc/cmdline); do
    case $x in
        home_link)
            data_link "home"
            data_link "root"
            ;;
        
        var_link)
            data_link "var"
            ;;
    esac
done

if [ -x "/root/preinit.sh" ]; then
    /root/preinit.sh
fi
