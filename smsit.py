"""
Check for hosts that are down.
Report by sending SMS

TODO: 
T) Needs to get smarter - too much spam if host is down
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
import os   # os.system(...)
import re   # Regular expressions (parse ping-output)
import time # time.sleep()
import sys  # ...
import ConfigParser

"""
Configuration: this part should be moved to
a configuration file (e.g. /etc/smsit.conf
"""

# List of hosts that should be checked
# Dictionary to keep all the host-objects
# Index is the ip-address of the host
hosts = {}

class host_object:
    ip_addr = ""       # ip address of host (same is index)
    hostname = ""      # hostname. Just your alias, can be anything.
    checks_failed = 0  # Number of checks failed

    def __init__(self,ip,name):
        self.ip_addr=ip
        self.hostname=name
        self.checks_failed=0

        # If no name is given in the config file, 
        # use the ip-address as name
        if name is "":
            self.hostname=ip
    
    def print_obj(self):
        print("[D] Name:   " + self.hostname)
        print("[D] Ip:     " + self.ip_addr)
        print("[D] Checks: " + str(self.checks_failed))
    

# Read config file
config = ConfigParser.ConfigParser()
config.read("smsit.conf")

# Get global variables
alert_treshold = int(config.get('global','alert_treshold'))
check_time = int(config.get('global','check_time'))
debug = int(config.get('global','debug'))
phone_no=config.get('global','phone_numbers').split(",")

# Get hosts
hostlist=config.items('hosts')
for h in hostlist:
    hosts[h[0]] = host_object(h[0],h[1])







"""
Util functions
"""
def print_hosts(hosts):
    s="Hosts:"
    for h in hosts:
        s+=" "+h
    INFO(s)


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
    for h in hosts:
        pingaling = os.popen("ping -q -W 5 -c2 " + h, "r") # do the ping
        sys.stdout.flush() 
        while 1:
            line = pingaling.readline()
            if not line: break 
            igot = re.findall(lifeline,line) # Parse
            if igot:
                INFO(h + " " + report[int(igot[0])])
                if int(igot[0]) == 0: hosts[h].checks_failed += 1
                else: hosts[h].checks_failed = 0
            #else: print "No igot ..."


# Return a list of all hosts that are down
# (Definition of down: have not responded to 
#  'ping' for the last number of checks. The number 
# is specified by alert_treshold.
# The amount of time a host has been down, depends
# on the alert_treshold and the time between each check 'check_time'
def host_down(hosts, alert_treshold):
    rl = [] # return value - list of hosts that are down
    for h in hosts:
        if hosts[h].checks_failed >= alert_treshold:
            rl.append(hosts[h].hostname)
    return rl
      
# We have at least one host that is down,
# and we want to send an alert.
# 'down' is a list of names of the hosts that are down
def alert(down):
    WARNING(str(len(down)) + " hosts are down!") 

    # Start message with 'host is down:'
    if len(down) == 1:
        down_str="1 host is down:\n"
    else:
        down_str=str(len(down))+" hosts are down:\n"

    # Append the list of names that are down 
    for d in down:
        down_str+=d+"\n"

    INFO("Alert sent. Length: "+str(len(down_str)))
    send_sms(down_str,phone_no)


# This method only checks message length, and takes care that
# the message is sent to all that are supposed to get it
def send_sms(msg, phone_numbers):
    # Check the length of the message (sms is small - like twitter!)
    if len(msg) > 160:
        WARNING("Message too long")

    # Do the message pass (finally)
    for p in phone_numbers:
        rv = os.system("echo \""+msg+"\" | gnokii --config /home/torjeh/.gnokiirc --sendsms "+str(p))

# Forever (or not)
print_hosts(hosts)
i=0
while (i<alert_treshold):
    i+=1
    test_ping_hosts(hosts)
    down = host_down(hosts, alert_treshold) # Check what hosts are down
    if len(down) > 0: # hosts are down
        alert(down)         
    else: 
        INFO("No hosts are confirmed down. No need to alarm - yet")

    time.sleep(check_time)



