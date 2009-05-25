"""
Check for hosts that are down.
Report by sending SMS


*) This program needs to run as root!
*) 


TODO: 
T) Make python 3.x compatible
T) Multithreaded? :)
T) Deamon
T) Config
T) Service
T) SMS-script


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
hosts = {"10.0.1.4":0, "127.0.0.1":0, "10.0.1.23":0}

# Phone number(s) (string or int, I don't care)
phone_no = [90912307] # Torje

# Number of checks a host must be down in a row to set off the alarm (send SMS)
alert_treshold = 3
# Number of minutes between each check
check_time = 5  # minutes
# Script to run to send the SMS (yeah, kind of diirty)
alert_sh = "./send_sms.sh"


""" Init: """ 
# Build dictionary that holds the hosts, and how many checks they have been down (in a row).


""" Body """

# This method is (pretty much) stolen from 
# http://www.wellho.net/solutions/python-python-threads-a-first-example.html
def test_ping_hosts(hosts):
    lifeline = re.compile(r"(\d) received")
    report = ("No response","Partial Response","Alive")
    #print "Testing " + str(len(hosts)) + " hosts."
    for h in hosts:
        pingaling = os.popen("ping -q -W 5 -c2 " + h, "r") # do the ping
        print h, 
        sys.stdout.flush() 
        while 1:
            line = pingaling.readline()
            if not line: break 
            igot = re.findall(lifeline,line) # Parse
            if igot:
                print report[int(igot[0])]
                if int(igot[0]) == 0: hosts[h] += 1
                else: hosts[h] = 0




def host_down(hosts, alert_treshold):
    rl = [] # return value - list of hosts that are down
    for h in hosts:
        if hosts[h] >= alert_treshold:
            rl.append(h)
    return rl
        
def alert(down):
    print str(len(down)) + " hosts are down!" 

# Forever
while (1):
    test_ping_hosts(hosts)
    down = host_down(hosts, alert_treshold) 
    if len(down) > 0: # hosts are down
        alert(down)         



    #for h in hosts:
    #   print h + " " + str(hosts[h])
