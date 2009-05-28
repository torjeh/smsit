#!/bin/sh
#
# Installscript for SMSit
# 
# I need to be run as root
#
#
# Change path of the executable
# =============================
# If you want to change the path of the executable, please rememer
# to do the changes in /etc/init.d/smsit as well
# 
# Change path of configuration file
# =================================
# The path of the configuration file (smsit.conf) is hardcoded into
# smsit.py, so please keep that in mind if you want to change the 
# location of the configuration file.

if [ `id -u` -ne 0 ] ; then
    echo "This script needs to be run as root to be able to install to default installation paths."
    exit 1
fi

install -v -m 755 -o root -g root smsit.py /usr/local/bin/
install -v -m 644 -o root -g root smsit.conf /etc/
install -v -m 755 -o root -g root smsit /etc/init.d/
update-rc.d smsit defaults


echo "Done!"
