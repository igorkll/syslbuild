# self update
to start self-updates, you need to call "/usr/local/sbin/self_update" from root and pass it the full path to the new .img file in the /data partition.  
you also need to set the size of all partitions as a constant, RATHER THAN calculating it using a standard formula when building an image.  
since the built-in update function is not able to increase the partitions size, you should set the size of all partitions from the very beginning with a margin for all future OTA updates.  
"size_boot_partition" and "size_root_partition" are two standard parameters that you need to change to do this.  
for production devices, I recommend allocating the BOOT/EFI partition size by at least 512 megabytes and rootfs by at least 10 gigabytes so that you can put all future updates.  