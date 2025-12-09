# remove unnecessary apt packages
apt purge -y npm nodejs
apt purge -y python3 perl mawk
apt autoremove -y --purge

# garbage after npm
rm -rf /root/.npm
rm -rf /home/*/.npm
rm -rf /usr/lib/node_modules
rm -rf /usr/local/lib/node_modules

# garbage collection from apt
apt clean
rm -rf /var/lib/apt/lists/*
rm -rf /var/cache/apt/archives/*

# removing apt & dpkg
apt purge -y \
  apt \
  apt-utils \
  aptitude \
  gnupg \
  gnupg2 \
  gpgv \
  dirmngr \
  dpkg-dev \
  debconf \
  software-properties-common \
  dpkg

rm -rf /etc/apt
rm -rf /var/lib/apt
rm -rf /var/cache/apt
rm -rf /usr/lib/apt

rm -f /usr/bin/apt /usr/bin/dpkg /usr/bin/apt-get /usr/bin/apt-cache

rm -rf /var/lib/dpkg
rm -rf /var/lib/debconf

rm -rf /etc/apt
rm -rf /etc/dpkg/
rm -rf /usr/lib/apt
rm -rf /var/lib/dpkg
rm -rf /usr/share/keyrings

rm -f /usr/bin/apt*
rm -f /usr/bin/dpkg*
rm -f /usr/bin/aptitude*
rm -f /usr/bin/add-apt-repository

rm -rf /var/cache/debconf
rm -rf /var/lib/debconf
rm -rf /usr/share/debconf

# removing system garbage
rm -rf /usr/share/doc/*
rm -rf /usr/share/man/*
rm -rf /usr/share/info/*
rm -rf /usr/share/locale/*

# removing electron locales
rm -rf /usr/lib/electron/locales

# removing garbage from temporary directories
find /tmp /var/tmp -mindepth 1 -delete

