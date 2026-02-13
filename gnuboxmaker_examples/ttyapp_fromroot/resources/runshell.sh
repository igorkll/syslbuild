#!/bin/bash

# disable tty hotkeys
stty intr undef   # Ctrl+C
stty quit undef   # Ctrl+\
stty stop undef   # Ctrl+S
stty start undef  # Ctrl+Q
stty susp undef   # Ctrl+Z

# disable echo mode
stty -echo

# clear screen and set cursor to first line
clear

# code
options=("Reboot" "Shutdown" "Bash")
selected=0

draw_menu() {
    clear
    echo "Use ↑ ↓ and SPACE"
    echo
    for i in "${!options[@]}"; do
        if [ "$i" = "$selected" ]; then
            echo "> ${options[i]}"
        else
            echo "  ${options[i]}"
        fi
    done
}

while true; do
    draw_menu
    IFS= read -rsn1 key

    if [[ $key == $'\x1b' ]]; then
        read -rsn2 key
        case $key in
            "[A") ((selected--)) ;;  # up
            "[B") ((selected++)) ;;  # down
        esac
    elif [[ $key == " " ]]; then
        case $selected in
            0) reboot --no-wall ;;
            1) shutdown --no-wall now ;;
            2)
                stty echo
                exec bash
                stty -echo
                ;;
        esac
        exit
    fi

    ((selected<0)) && selected=$((${#options[@]}-1))
    ((selected>=${#options[@]})) && selected=0
done
