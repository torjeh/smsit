"""
Check for hosts that are down.
Report by sending SMS


We could make this application multithreaded,
but there is no use at this point.

*) This program needs to run as root!
*) This program is python 3.x compatible
*) 


Torje S. Henriksen
torje.starbo.henriksen@telemed.no

"""

""" Imports """
import os
import re
import time
import sys

"""
Configuration: this part should be moved to
a configuration file (e.g. /etc/smsit.conf
"""

# List of hosts that should be checked
hosts = {"pbg4.local":0, "localhost":0, "somebody":0}

# Phone number(s) (string or int, I don't care)
phone_no = [90912307] # Torje

# Number of checks a host must be down in a row to set off the alarm (send SMS)
alarm_treshold = 3
# Number of minutes between each check
check_time = 5  # minutes
# Script to run to send the SMS (yeah, kind of diirty)
alert_sh = "/home/torjeh/local/bin/send_sms.sh"


""" Init: """ 
# Build dictionary that holds the hosts, and how many checks they have been down (in a row).


""" Body """

# This method is stolen from 
# http://www.wellho.net/solutions/python-python-threads-a-first-example.html

def test_ping_hosts(hosts):
    lifeline = re.compile(r"(\d) received")
    report = ("No response","Partial Response","Alive")
    print "Testing " + str(len(hosts)) + " hosts."
    for h in hosts:
        pingaling = os.popen("ping -q -c2 " + h, "r") # do the ping
        print h, 
        sys.stdout.flush() #?
        while 1:
            line = pingaling.readline()
            if not line: break
            igot = re.findall(lifeline,line)
            if igot:
                print report[int(igot[0])]
    print time.ctime()

test_ping_hosts(hosts)

for h in hosts:
    print h + " " + str(hosts[h])
