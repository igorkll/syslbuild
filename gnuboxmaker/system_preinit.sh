#!/bin/sh

data_merge_overwrite() {

}

data_link() {
	if [ ! -d "/root/data/$1" ]; then
        /nativeucp -a "/root/$1" "/root/data/$1"
    fi

    /nativemount --bind "/root/data/$1" "/root/$1"
}

for x in $(cat /root/proc/cmdline); do
    case $x in
        home_merge_overwrite)
            data_merge_overwrite "home"
            data_merge_overwrite "root"
            ;;
        
        home_merge_overwrite)
            data_merge_overwrite "var"
            ;;

        etc_merge_overwrite)
            data_merge_overwrite "etc"
            ;;
    esac
done

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
