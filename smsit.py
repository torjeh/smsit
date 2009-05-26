"""
Check for hosts that are down.
Report by sending SMS

TODO: 
T) Deamon
T) Service
T) Config
T) Signal-handling
T) SMS-script
T) Make python 3.x compatible
T) Multithreaded? :)
T) Support more than ping?
   - dhcp,dns 

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

hosts = {\
"127.0.0.1":0,\
"10.0.1.4":0,\
"172.21.14.130":0,\
"10.0.1.5":0\
}
# Phone number(s) (string or int, I don't care)
phone_no = [90912307] # Torje

# Number of checks a host must be down in a row to set off the alarm (send SMS)
alert_treshold = 3
# Number of minutes between each check
check_time = 5  # minutes

# Script to run to send the SMS (yeah, kind of diirty)
alert_sh = "./send_sms.sh"

# Debug enabled?
debug = 1

""" Init: Read the config file into memory. 
""" 



"""
Util functions
"""
def print_hosts(hosts):
    print("Hosts: "),
    for h in hosts:
        print(h+" "),
    print("") # newline

# printout functions. Should be put into
# a log eventually. /var/log/smsit.log (?)
def DEBUG(s):
    global debug
    if debug:
        print("[D] " +str(s))
def INFO(s):
    print("[I] " + str(s))
def WARNING(s):
    print("[W] " + str(s))
def ERROR(s):
    print("[E] " + str(s))


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
            #else: print "No igot ..."

def host_down(hosts, alert_treshold):
    rl = [] # return value - list of hosts that are down
    for h in hosts:
        if hosts[h] >= alert_treshold:
            rl.append(h)
    return rl
        
# We have at least one host that is down,
# and we want to send an alert.
def alert(down):
    print str(len(down)) + " hosts are down!" 
    rv = os.system("echo \"This is where we send an SMS\"")
    down_str="These hosts are down:\n"
    for d in down:
        down_str+=str(d)+"\n"

    INFO("Alert sent. Length: "+str(len(down_str)))
    send_sms(down_str)

def send_sms(msg):
    if len(msg) > 150:
        WARNING("Message too long")
    os.system("echo \""+msg+"\" | gnokii --config /home/torjeh/.gnokiirc --sendsms 90912307")

# Forever (or not)
print_hosts(hosts)
i=0
while (i<3):
    i+=1
    test_ping_hosts(hosts)
    down = host_down(hosts, alert_treshold) # Check if host is really down
    if len(down) > 0: # hosts are down
        alert(down)         
    else: 
        INFO("No hosts are down")


    #for h in hosts:
    #   print h + " " + str(hosts[h])
