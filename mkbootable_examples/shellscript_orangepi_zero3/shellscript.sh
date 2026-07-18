#!/bin/bash

export PATH="/sbin:$PATH"

# ----------- functions

tty_black=0
tty_red=1
tty_green=2
tty_yellow=3
tty_blue=4
tty_purple=5
tty_cyan=6
tty_white=7
tty_h_black=8
tty_h_red=9
tty_h_green=10
tty_h_yellow=11
tty_h_blue=12
tty_h_purple=13
tty_h_cyan=14
tty_h_white=15

tty_set_color() {
    local fg=$1
    local bg=$2
    if (( fg >= 8 )); then
        fg=$(( (fg - 8) + 90 ))
    else
        fg=$(( fg + 30 ))
    fi
    if (( bg >= 8 )); then
        bg=$(( (bg - 8) + 100 ))
    else
        bg=$(( bg + 40 ))
    fi

    echo -ne "\033[0;${fg};${bg}m"
}

tty_clear() {
    clear
}

tty_set_cursor() {
    local x=$1
    local y=$2
    echo -ne "\033[${y};${x}H"
}

tty_fill() {
    local x=$1
    local y=$2
    local w=$3
    local h=$4
    local char=$5

    line=""
    for ((i=0;i<w;i++)); do
        line+="$char"
    done

    for ((i=0;i<h;i++)); do
        tty_set_cursor $x $(( y + i ))
        echo -ne "$line"
    done
}

tty_text() {
    local x=$1
    local y=$2
    local text=$3

    tty_set_cursor $x $y
    echo -ne "$text"
}

tty_rtext() {
    local x=$1
    local y=$2
    local text=$3

    tty_text $(( x - (${#text} - 1) )) $y "$text"
}

tty_ctext() {
    local x=$1
    local y=$2
    local text=$3

    tty_text $(( x - (${#text} / 2) + 1 )) $y "$text"
}

tty_setRawMode() {
    local flag=$1
    if (( flag > 0 )); then
        stty raw -echo

        stty intr undef
        stty quit undef
        stty susp undef

        stty -ixon
        stty -ixoff
    else
        stty sane
    fi
}

tty_setCusrorBlick() {
    local flag=$1
    if (( flag > 0 )); then
        echo -ne "\033[?25h"
    else
        echo -ne "\033[?25l"
    fi
}

# ----------- shell

menuOpened=0
menuOpenedMode=0

appsMenu_index=0
appsMenu_names=(
    "bash"
    "lua"
    "python"
    "disk manager"
    "browser"
)
appsMenu_commands=(
  "bash"
  "lua"
  "python3"
  "@disk_manager"
  "@browser"
)

systemMenu_index=0
systemMenu_names=(
    "poweroff"
    "reboot"
)
systemMenu_commands=(
  "poweroff"
  "reboot"
)

draw_menu() {
    local x=$1
    local y=$2
    local w=$3
    local h=$4
    local x2=$(( x + (w - 1) ))
    local y2=$(( y + (h - 1) ))

    tty_set_color $tty_h_white $tty_h_black
    tty_fill $x $y $w $h " "

    local pos=2
    for i in "${!systemMenu_names[@]}"; do
        name="${systemMenu_names[$i]}"
        if (( i == systemMenu_index && menuOpenedMode == 1 )); then
            tty_set_color $tty_h_blue $tty_h_black
        else
            tty_set_color $tty_h_white $tty_h_black
        fi
        tty_text $pos $y2 $name
        pos=$(( pos + ${#name} + 1 ))
    done

    local pos=$(( y + 1 ))
    for i in "${!appsMenu_names[@]}"; do
        name="${appsMenu_names[$i]}"
        if (( i == appsMenu_index && menuOpenedMode == 0 )); then
            tty_set_color $tty_h_blue $tty_h_black
        else
            tty_set_color $tty_h_white $tty_h_black
        fi
        tty_text $(( x + 1 )) $pos "$name"
        pos=$(( pos + 1 ))
    done

}

draw_desktop() {
    # background
    tty_set_color $tty_h_white $tty_cyan
    clear

    # logo
    local logoWidth=20
    local logoHeight=5
    tty_ctext $(( COLUMNS / 2 )) $(( (LINES / 2) + 1 )) "mikonanoOS"

    # dock
    tty_set_color $tty_h_white $tty_green
    tty_fill 1 $LINES $COLUMNS 1 " "
    tty_rtext $(( COLUMNS - 1 )) $LINES "$( date )"

    if (( menuOpened > 0 )); then
        tty_set_color $tty_h_white $tty_h_yellow
    else
        tty_set_color $tty_h_white $tty_yellow
    fi
    tty_text 1 $LINES " @@ "

    # menu
    if (( menuOpened > 0 )); then
        draw_menu 1 $(( $LINES - 20 )) 40 20
    fi
}

handle_menu() {
    local key=$1
    case "$key" in
        $'\x1b')
            read -rsn2 -t 0.01 rest
            case "$rest" in
                '[A')
                    # up
                    if (( menuOpenedMode == 0 )); then
                        appsMenu_index=$(( appsMenu_index - 1 ))
                        if (( appsMenu_index < 0 )); then
                            appsMenu_index=$(( ${#appsMenu_names[@]} - 1 ))
                        fi
                    else
                        menuOpenedMode=0
                        appsMenu_index=0
                    fi
                    ;;
                
                '[B')
                    # down
                    if (( menuOpenedMode == 0 )); then
                        appsMenu_index=$(( appsMenu_index + 1 ))
                        if (( appsMenu_index >= ${#appsMenu_names[@]} )); then
                            appsMenu_index=0
                        fi
                    else
                        menuOpenedMode=0
                        appsMenu_index=0
                    fi
                    ;;
                
                '[D')
                    # left
                    if (( menuOpenedMode == 1 )); then
                        systemMenu_index=$(( systemMenu_index - 1 ))
                        if (( systemMenu_index < 0 )); then
                            systemMenu_index=$(( ${#systemMenu_names[@]} - 1 ))
                        fi
                    else
                        menuOpenedMode=1
                        systemMenu_index=0
                    fi
                    ;;

                '[C')
                    # right
                    if (( menuOpenedMode == 1 )); then
                        systemMenu_index=$(( systemMenu_index + 1 ))
                        if (( systemMenu_index >= ${#systemMenu_names[@]} )); then
                            systemMenu_index=0
                        fi
                    else
                        menuOpenedMode=1
                        systemMenu_index=0
                    fi
                    ;;
                
                '')
                    # esc
                    menuOpened=0
                    ;;
                
                *)
                    ;;
            esac
            ;;
    esac
}

disk_manager() {
    mapfile -t rawdisks < <(
        lsblk -dn -o NAME,TYPE |
        awk '$2=="disk" || $2=="rom"{print "/dev/"$1}'
    )

    if (( ${#rawdisks[@]} == 0 )); then
        dialog --msgbox "No disks or CD/DVD devices found." 7 40
        return 0
    fi
    
    mapfile -t disks < <(
        lsblk -dn -o NAME,TYPE,SIZE,RO,MODEL |
        awk '$2=="disk" || $2=="rom"'
    )

    local args=()
    local id=1
    for line in "${disks[@]}"; do
        read -r name type size ro model <<< "$line"

        dev="/dev/$name"

        ro_flag=""
        [[ "$ro" == "1" ]] && ro_flag="(RO) "

        args+=(
            "$id"
            "$dev [$type] ${ro_flag}$size $model"
        )
        id=$((id + 1))
    done
    
    local disk_id=$(dialog --stdout --menu "Select disk:" 0 0 0 "${args[@]}")
    if [[ -z "$disk_id" ]]; then
        return 0
    fi

    disk_id=$(( disk_id - 1 ))
    local disk="${rawdisks[disk_id]}"

    if [[ "$(lsblk -dn -o RO "$disk")" == "1" ]]; then
        dialog --msgbox "Disk $disk is read-only." 7 40
        return 0
    fi

    if [[ -n "$disk" ]]; then
        cfdisk "$disk"
    fi
}

browser() {
    dialog --title "Open URL" --inputbox "Enter URL:" 10 50 2> /tmp/url.txt

    if [[ $? -ne 0 ]]; then
        return 0
    fi

    URL=$(< /tmp/url.txt)
    w3m "$URL"
}

handle_menu_app() {
    if (( menuOpenedMode == 0 )); then
        cmd="${appsMenu_commands[$appsMenu_index]}"
        tty_set_color tty_h_white tty_h_black
        clear
        tty_setRawMode 0
        tty_setCusrorBlick 1
        if [[ "$cmd" == @* ]]; then
            func_name="${cmd#@}"
            "$func_name"
        else
            setsid bash -c "$cmd"
        fi
        tty_setRawMode 1
        tty_setCusrorBlick 0
    elif (( menuOpenedMode == 1 )); then
        cmd="${systemMenu_commands[$systemMenu_index]}"
        eval "$cmd"
    fi
}

handle_desktop() {
    read -rsn1 key
    case "$key" in
        $'\x7f'|$'\x08')
            # backspace
            exit
            ;;
        
        $'\x00'|$'\r'|$'\n')
            # space / enter
            if (( menuOpened > 0 )); then
                handle_menu_app
            fi
            menuOpened=$(( 1 - menuOpened ))
            ;;
        
        *)
            ;;
    esac

    if (( menuOpened > 0 )); then
        handle_menu $key
    fi
}

tty_setRawMode 1
tty_setCusrorBlick 0

while :; do
    draw_desktop
    handle_desktop
done

tty_setRawMode 0
tty_setCusrorBlick 1


