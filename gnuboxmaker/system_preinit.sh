#!/bin/bash

data_merge_add() {
    local dir="$1"
    /nativechroot /root /usr/bin/rsync -aHAX --copy-dirlinks --ignore-existing "/$dir/" "/data/$dir/"
}

data_merge_overwrite() {
    local dir="$1"
    /nativechroot /root /usr/bin/rsync -aHAX --copy-dirlinks "/$dir/" "/data/$dir/"
}

data_link() {
	if [ ! -d "/root/data/$1" ]; then
        /nativeucp -a "/root/$1" "/root/data/$1"
    fi

    /nativemount --bind "/root/data/$1" "/root/$1"
}

if [ -e "/root/data/after_update_or_first_start.flag" ]; then
    for x in $(cat /root/proc/cmdline); do
        case $x in
            home_merge_add)
                data_merge_add "home"
                data_merge_add "root"
                ;;
            
            var_merge_add)
                data_merge_add "var"
                ;;

            etc_merge_add)
                data_merge_add "etc"
                ;;
        esac
    done

    for x in $(cat /root/proc/cmdline); do
        case $x in
            home_merge_overwrite)
                data_merge_overwrite "home"
                data_merge_overwrite "root"
                ;;
            
            var_merge_overwrite)
                data_merge_overwrite "var"
                ;;

            etc_merge_overwrite)
                data_merge_overwrite "etc"
                ;;
        esac
    done

    rm -f /root/data/after_update_or_first_start.flag
fi

for x in $(cat /root/proc/cmdline); do
    case $x in
        home_link)
            data_link "home"
            data_link "root"
            ;;
        
        var_link)
            data_link "var"
            ;;

        etc_link)
            data_link "etc"
            ;;
    esac
done

if [ -x "/root/gnubox/preinit.sh" ]; then
    /root/gnubox/preinit.sh
fi

sync
