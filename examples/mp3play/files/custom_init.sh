#!/bin/sh

# Default PATH differs between shells, and is not automatically exported
# by klibc dash.  Make it consistent.
export PATH=/sbin:/usr/sbin:/bin:/usr/bin

[ -d /proc ] || mkdir /proc
mount -t proc -o nodev,noexec,nosuid proc /proc

for x in $(cat /proc/cmdline); do
	case $x in
	quiet)
		quiet=y
		;;

	# custom init parameters
	clear)
		printf "\033[2J\033[H"
		;;
	noCursorBlink)
		printf "\033[?25l"
		;;
	earlysplash)
		EARLYSPLASH=true
		;;
	noctrlaltdel)
		echo 0 > /proc/sys/kernel/ctrl-alt-del
		;;
	nosysrq)
		echo 0 > /proc/sys/kernel/sysrq
		;;
	esac
done

[ -d /dev ] || mkdir -m 0755 /dev
[ -d /root ] || mkdir -m 0700 /root
[ -d /sys ] || mkdir /sys
[ -d /tmp ] || mkdir /tmp
mkdir -p /var/lock
mount -t sysfs -o nodev,noexec,nosuid sysfs /sys
mount -t tmpfs -o "nodev,nosuid,size=${RUNSIZE:-10%},mode=1777" tmpfs /tmp

if [ "$quiet" != "y" ]; then
	quiet=n
	echo "Loading, please wait..."
fi
export quiet

# Note that this only becomes /dev on the real filesystem if udev's scripts
# are used; which they will be, but it's worth pointing out
mount -t devtmpfs -o nosuid,mode=0755 udev /dev

# Prepare the /dev directory
[ ! -h /dev/fd ] && ln -s /proc/self/fd /dev/fd
[ ! -h /dev/stdin ] && ln -s /proc/self/fd/0 /dev/stdin
[ ! -h /dev/stdout ] && ln -s /proc/self/fd/1 /dev/stdout
[ ! -h /dev/stderr ] && ln -s /proc/self/fd/2 /dev/stderr

mkdir /dev/pts
mount -t devpts -o noexec,nosuid,gid=5,mode=0620 devpts /dev/pts || true
mount -t tmpfs -o "nodev,noexec,nosuid,size=${RUNSIZE:-10%},mode=0755" tmpfs /run

plymouth_init() {
	mkdir -m 0755 /run/plymouth
	/usr/sbin/plymouthd --mode=boot --attach-to-session --pid-file=/run/plymouth/pid
	/usr/bin/plymouth --show-splash
}

# initialization of plymouth has been moved to an earlier stage
if [ "${EARLYSPLASH}" = "true" ]
then
	if [ -e /dev/fb0 ]; then
		plymouth_init
		PLYMOUTH_FAILED=false
	else
		PLYMOUTH_FAILED=true
	fi
fi

# Export the dpkg architecture
export DPKG_ARCH=
. /conf/arch.conf

# Set modprobe env
export MODPROBE_OPTIONS="-qb"

# Export relevant variables
export ROOT=
export ROOTDELAY=
export ROOTFLAGS=
export ROOTFSTYPE=
export IP=
export DEVICE=
export BOOT=
export BOOTIF=
export UBIMTD=
export break=
export init=/sbin/init
export readonly=y
export rootmnt=/root
export debug=
export panic=
export blacklist=
export resume=
export resume_offset=
export noresume=
export drop_caps=
export fastboot=n
export forcefsck=n
export fsckfix=


# Bring in the main config
. /conf/initramfs.conf
for conf in conf/conf.d/*; do
	[ -f "${conf}" ] && . "${conf}"
done
. /scripts/functions

# Parse command line options
# shellcheck disable=SC2013
for x in $(cat /proc/cmdline); do
	case $x in
	init=*)
		init=${x#init=}
		;;
	root=*)
		ROOT=${x#root=}
		if [ -z "${BOOT}" ] && [ "$ROOT" = "/dev/nfs" ]; then
			BOOT=nfs
		fi
		;;
	rootflags=*)
		ROOTFLAGS="-o ${x#rootflags=}"
		;;
	rootfstype=*)
		ROOTFSTYPE="${x#rootfstype=}"
		;;
	rootdelay=*)
		ROOTDELAY="${x#rootdelay=}"
		case ${ROOTDELAY} in
		*[![:digit:].]*)
			ROOTDELAY=
			;;
		esac
		;;
	nfsroot=*)
		# shellcheck disable=SC2034
		NFSROOT="${x#nfsroot=}"
		;;
	initramfs.runsize=*)
		RUNSIZE="${x#initramfs.runsize=}"
		;;
	ip=*)
		IP="${x#ip=}"
		;;
	boot=*)
		BOOT=${x#boot=}
		;;
	ubi.mtd=*)
		UBIMTD=${x#ubi.mtd=}
		;;
	resume=*)
		RESUME="${x#resume=}"
		;;
	resume_offset=*)
		resume_offset="${x#resume_offset=}"
		;;
	noresume)
		noresume=y
		;;
	drop_capabilities=*)
		drop_caps="-d ${x#drop_capabilities=}"
		;;
	panic=*)
		panic="${x#panic=}"
		;;
	ro)
		readonly=y
		;;
	rw)
		readonly=n
		;;
	debug)
		debug=y
		quiet=n
		if [ -n "${netconsole}" ]; then
			log_output=/dev/kmsg
		else
			log_output=/run/initramfs/initramfs.debug
		fi
		set -x
		;;
	debug=*)
		debug=y
		quiet=n
		set -x
		;;
	break=*)
		break=${x#break=}
		;;
	break)
		break=premount
		;;
	blacklist=*)
		blacklist=${x#blacklist=}
		;;
	netconsole=*)
		netconsole=${x#netconsole=}
		[ "$debug" = "y" ] && log_output=/dev/kmsg
		;;
	BOOTIF=*)
		BOOTIF=${x#BOOTIF=}
		;;
	fastboot|fsck.mode=skip)
		fastboot=y
		;;
	forcefsck|fsck.mode=force)
		forcefsck=y
		;;
	fsckfix|fsck.repair=yes)
		fsckfix=y
		;;
	fsck.repair=no)
		fsckfix=n
		;;
	splash*)
		SPLASH="true"
		;;
	nosplash*|plymouth.enable=0)
		SPLASH="false"
		;;

	# it doesn't seem to be working at all. So I'll make my own
	initramfs.clear)
		clear
		;;
	
	# custom init parameters
	loop=*)
		LOOP="${x#loop=}"
		;;
	loopflags=*)
		LOOPFLAGS="-o ${x#loopflags=}"
		;;
	loopfstype=*)
		LOOPFSTYPE="${x#loopfstype=}"
		;;
	loopreadonly=y)
		LOOPREADONLY=y
		;;
	
	makevartmp)
		makevartmp=true
		;;
	makehometmp)
		makehometmp=true
		;;
	makeroothometmp)
		makeroothometmp=true
		;;
		
	logodelay=*)
		LOGODELAY="${x#logodelay=}"
		case ${LOGODELAY} in
		*[![:digit:].]*)
			LOGODELAY=
			;;
		esac
		;;

	root_processing=y)
		ROOT_PROCESSING=y
		;;
	root_expand=y)
		ROOT_EXPAND=y
		;;
	esac
done

# Default to BOOT=local if no boot script defined.
if [ -z "${BOOT}" ]; then
	BOOT=local
fi

if [ -n "${noresume}" ] || [ "$RESUME" = none ]; then
	noresume=y
else
	resume=${RESUME:-}
fi

mkdir -m 0700 /run/initramfs

if [ -n "$log_output" ]; then
	exec >"$log_output" 2>&1
	unset log_output
fi

maybe_break top

# Don't do log messages here to avoid confusing graphical boots
run_scripts /scripts/init-top

maybe_break modules
[ "$quiet" != "y" ] && log_begin_msg "Loading essential drivers"
[ -n "${netconsole}" ] && /sbin/modprobe netconsole netconsole="${netconsole}"
load_modules
[ "$quiet" != "y" ] && log_end_msg

if [ "${PLYMOUTH_FAILED}" = "true" ]
then
	if [ -e /dev/fb0 ]; then
		plymouth_init
		PLYMOUTH_FAILED=false
	else
		PLYMOUTH_FAILED=true
	fi
fi

starttime="$(_uptime)"
starttime=$((starttime + 1)) # round up
export starttime

if [ "$ROOTDELAY" ]; then
	sleep "$ROOTDELAY"
fi

maybe_break premount
[ "$quiet" != "y" ] && log_begin_msg "Running /scripts/init-premount"
run_scripts /scripts/init-premount
[ "$quiet" != "y" ] && log_end_msg

maybe_break mount
log_begin_msg "Mounting root file system"
# Always load local and nfs (since these might be needed for /etc or
# /usr, irrespective of the boot script used to mount the rootfs).
. /scripts/local
. /scripts/nfs
. "/scripts/${BOOT}"
parse_numeric "${ROOT}"
maybe_break mountroot
mount_top
mount_premount

if [ "${PLYMOUTH_FAILED}" = "true" ]
then
	if [ -e /dev/fb0 ]; then
		plymouth_init
		PLYMOUTH_FAILED=false
	else
		PLYMOUTH_FAILED=true
	fi
fi

# custom init paramenters
if [ "$LOGODELAY" ]; then
	sleep "$LOGODELAY"
fi

if [ -n "$ROOT" ] && [ -n "$ROOT_PROCESSING" ]; then
	local_device_setup "${ROOT}" "root file system"
	PART_NUM="${DEV##*[!0-9]}"
	DISK="${DEV%$PART_NUM}"
	
	if [ -n "$ROOT_EXPAND" ]; then
		log_begin_msg "Expanding root partition"
		growpart "$DISK" "$PART_NUM"
		resize2fs "$DEV"
		log_end_msg
	fi
fi

if [ -n "$LOOP" ]; then
	mountroot()
	{
		log_begin_msg "Mount loop root filesystem"

		if [ -n "$ROOT" ]; then
			if [ "$BOOT" = "nfs" ]; then
				nfs_mount_root
			else
				local_mount_root
			fi

			mkdir -m 0700 /realroot
			mount -n -o move "${rootmnt}" /realroot
		fi

		if [ "$readonly" = y ]; then
			roflag=-r
		else
			if [ -n "$LOOPREADONLY" ]; then
				roflag=-r
			else
				roflag=-w
			fi
		fi

		FSTYPE="$LOOPFSTYPE"
		if [ -z "$FSTYPE" ] || [ "$FSTYPE" = "unknown" ]; then
			FSTYPE=$(/sbin/blkid -s TYPE -o value "$LOOP")
			[ -z "$FSTYPE" ] && FSTYPE="unknown"
		fi

		modprobe loop
		mknod /dev/loop-root b 7 0
		losetup /dev/loop-root "$LOOP"
		mount ${roflag} -t ${FSTYPE} ${LOOPFLAGS} /dev/loop-root "${rootmnt}"

		if [ -d "/realroot" ] && [ -d "${rootmnt}/realroot" ]; then
			mount -n -o move /realroot ${rootmnt}/realroot
		fi

		log_end_msg
	}
fi

mountroot
log_end_msg

if read_fstab_entry /usr; then
	log_begin_msg "Mounting /usr file system"
	mountfs /usr
	log_end_msg
fi

# Mount cleanup
mount_bottom
nfs_bottom
local_bottom

maybe_break bottom
[ "$quiet" != "y" ] && log_begin_msg "Running /scripts/init-bottom"
# We expect udev's init-bottom script to move /dev to ${rootmnt}/dev
run_scripts /scripts/init-bottom
[ "$quiet" != "y" ] && log_end_msg

# Move /run to the root
mount -n -o move /run ${rootmnt}/run

validate_init() {
	run-init -n "${rootmnt}" "${1}"
}

# Check init is really there
if ! validate_init "$init"; then
	echo "Target filesystem doesn't have requested ${init}."
	init=
	for inittest in /sbin/init /etc/init /bin/init /bin/sh; do
		if validate_init "${inittest}"; then
			init="$inittest"
			break
		fi
	done
fi

# No init on rootmount
if ! validate_init "${init}" ; then
	panic "No init found. Try passing init= bootarg."
fi

maybe_break init

# don't leak too much of env - some init(8) don't clear it
# (keep init, rootmnt, drop_caps)
unset debug
unset MODPROBE_OPTIONS
unset DPKG_ARCH
unset ROOTFLAGS
unset ROOTFSTYPE
unset ROOTDELAY
unset ROOT
unset IP
unset BOOT
unset BOOTIF
unset DEVICE
unset UBIMTD
unset blacklist
unset break
unset noresume
unset panic
unset quiet
unset readonly
unset resume
unset resume_offset
unset noresume
unset fastboot
unset forcefsck
unset fsckfix
unset starttime

make_temp() {
	local dirname=$1
	local olddir="/${dirname}.old"
	local target="${rootmnt}/${dirname}/"

	if [ -d "${target}" ]; then
		mkdir -p "$olddir"
		mount -t tmpfs tmpfs "$olddir"
		cp -a "${target}/." $olddir
		mount -t tmpfs -o mode=1777,nodev,nosuid tmpfs "$target"
		cp -a "${olddir}/." $target
		umount "$olddir"
		rm -rf "$olddir"
	fi
}

# make /var tmpfs
if [ "$makevartmp" = "true" ]; then
	make_temp "var"
fi

# make /home tmpfs
if [ "$makehometmp" = "true" ]; then
	make_temp "home"
fi

# make /root tmpfs
if [ "$makeroothometmp" = "true" ]; then
	make_temp "root"
fi

# Move virtual filesystems over to the real filesystem
mount -n -o move /sys ${rootmnt}/sys
mount -n -o move /proc ${rootmnt}/proc
mount -n -o move /tmp ${rootmnt}/tmp

# Chain to real filesystem
# shellcheck disable=SC2086,SC2094
exec run-init ${drop_caps} "${rootmnt}" "${init}" "$@" <"${rootmnt}/dev/console" >"${rootmnt}/dev/console" 2>&1
echo "Something went badly wrong in the initramfs."
panic "Please file a bug on initramfs-tools."

