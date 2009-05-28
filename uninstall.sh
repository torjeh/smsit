#!/bin/sh
#
# uninstallscript for SMSit
# 
# I need to be run as root
#
#
#

if [ `id -u ` -ne 0 ] ; then
    echo "This script needs to be run as root to be able to install to default installation paths."
    exit 1
fi

rm -v /usr/local/bin/smsit.py
rm -v /etc/smsit.conf
rm -v /etc/init.d/smsit
update-rc.d -f smsit remove

echo "Done!"
