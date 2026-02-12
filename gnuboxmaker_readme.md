# Gnubox maker
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/gnuboxmaker_preview.png)  
the easiest way is to create an embedded/kiosk linux distribution with a single application that cannot be exited  
it uses a patched linux kernel, which prevents switching VT and using ctrl+alt+del  

## what was disabled
* ESC button in plymouth (source code patch)
* ctrl+alt+del in the linux kernel (source code patch)
* switching VT (source code patch + configs)