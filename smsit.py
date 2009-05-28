"""
Check for hosts that are down.
Report by sending SMS

TODO: 
T) Service
T) Signal-handling
T) Write pid to pidfile
T) Multithreaded? :)
T) Support more than ping?
   - dhcp,dns 
Torje S. Henriksen
torje.starbo.henriksen@telemed.no

"""

""" Imports """
import os   # os.system(...)
import re   # Regular expressions (parse ping-output)
from time import strftime, localtime, sleep, ctime
import sys  # ...
import ConfigParser # Read config file
import signal # should catch signals to die gracefully


# File descriptor for logfile
lf=None

class host_object:
    ip_addr = ""       # ip address of host (same as index to the hosts-dictionary)
    hostname = ""      # hostname. Just your alias, can be anything.
    checks_failed = 0  # Number of checks failed
    alert_sent = 0     # Has an alert been sent for this host?

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
    
"""
Util functions
"""
def print_hosts(hosts):
    s="Hosts:"
    for h in hosts:
        s+=" "+h
    INFO(s)


# This function handles all incoming signals
# (Pretty much just to shut down)
# http://docs.python.org/library/signal.html
def signal_handler(signum, frame):
    INFO("Someone is shutting us down with signal: " + str(signum))
    lf.close()
    sys.exit()

def now():
    return str(strftime("%b %d %H:%M:%S ", localtime()))

# printout functions. Should be put into
# a log eventually. /var/log/smsit.log (?)
def DEBUG(s):
    global debug
    if debug:
        lf.write(now()+"[D] " +str(s))
        lf.write("\n")
        lf.flush()
def INFO(s):
    lf.write(now()+"[I] " + str(s))
    lf.write("\n")
    lf.flush()
def WARNING(s):
    lf.write(now()+"[W] " + str(s))
    lf.write("\n")
    lf.flush()
def ERROR(s):
    lf.write(now()+"[E] " + str(s))
    lf.write("\n")
    lf.flush()



"""
Init: This is where we read the config file, and create our objects
"""

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM,signal_handler)

# List of hosts that should be checked
# Index is the ip-address of the host
hosts = {}

# Read config file
# ConfigParser is included in python and
# documented here http://www.python.org/doc/2.6.2/library/configparser.html
config = ConfigParser.ConfigParser()
config.read("smsit.conf") # Hardcoded config file ... 
    
# Get global variables from config file
alert_treshold = int(config.get('global','alert_treshold')) # int
check_time = int(config.get('global','check_time')) # int
debug = int(config.get('global','debug')) # int
phone_no=config.get('global','phone_numbers').split(",") # Comma-separated list
daemon=int(config.get('global','daemon')) # int
gnokiiconfig=config.get('global','gnokiiconfig') # str
logfile=config.get('global','logfile') # str
pidfile=config.get('global','pidfile') # str

# Get hosts
hostlist=config.items('hosts')
for h in hostlist:
    hosts[h[0]] = host_object(h[0],h[1])

# Go into daemonized form
if daemon:
    print("Becoming a daemon ...")
    from daemonize import createDaemon
    createDaemon()
    # Open log-file (in appending mode)
    lf=open(logfile,'a') 


INFO("SMSit started " + ctime())
DEBUG("##################### ")
DEBUG("### Configuration ### ")
DEBUG("##################### ")
DEBUG("alert_treshold: " + str(alert_treshold))
DEBUG("check_time:     " + str(check_time))
DEBUG("debug:          " + str(debug))
DEBUG("phone_no:       " + str(phone_no))
DEBUG("daemon:         " + str(daemon))
DEBUG("gnokiiconfig:   " + str(gnokiiconfig))
DEBUG("logfile:        " + str(logfile))
DEBUG("pidfile:        " + str(pidfile))
DEBUG("workingdir:     " + str(os.getcwd())
DEBUG("My pid:         " + str(os.getpid()))
DEBUG("##################### ")

""" Body """

# This method is (pretty much) stolen from 
# http://www.wellho.net/solutions/python-python-threads-a-first-example.html
def test_ping_hosts(hosts):
    t0 = time.time()
    lifeline = re.compile(r"(\d) received")
    report = ("No response","Partial Response","Alive")
    for h in hosts:
        pingaling = os.popen("ping -q -w 5 -c2 " + h, "r") # do the ping
        #sys.stdout.flush() 
        while 1:
            line = pingaling.readline()
            if not line: break 
            igot = re.findall(lifeline,line) # Parse
            if igot:
                INFO(h + " " + report[int(igot[0])])
                # Host is down
                if int(igot[0]) == 0: 
                    hosts[h].checks_failed += 1
                # Host is up
                else: 
                    hosts[h].checks_failed = 0
                    hosts[h].alert_sent = 0
            #else: print "No igot ..."
    time_taken=time.time()-t0
    DEBUG("Spent " + str(time_taken) " pinging hosts")


# Return a list of all hosts that are down
# (Definition of down: have not responded to 
#  'ping' for the last number of checks. The number 
# is specified by alert_treshold.
# The amount of time a host has been down, depends
# on the alert_treshold and the time between each check 'check_time'
def host_down(hosts, alert_treshold):
    rl = {} # return value - list of hosts that are down
    for h in hosts:
        if hosts[h].checks_failed >= alert_treshold:
            rl[h] = hosts[h]
    return rl
      
# Alert is called if we have at least one host 
# that is down, and we want to send an alert.
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
        down_str+=down[d].hostname+"\n"

    INFO("Sending alert. Length: "+str(len(down_str)))
    send_sms(down_str,phone_no)


# send_sms takes care that
# the message is sent to all that are supposed to get it
def send_sms(msg, phone_numbers):
    # Check the length of the message (sms is small - like twitter!)
    if len(msg) > 160:
        WARNING("Message too long")

    # Do the message pass (finally)
    for p in phone_numbers:
        rv = os.system("echo \""+msg+"\" | gnokii --config " + gnokiiconfig +" --sendsms "+str(p))


"""
Loop forever (Or until CTRL-C hopefully)
"""
while 1:
    test_ping_hosts(hosts)
    down = host_down(hosts, alert_treshold) # Check what hosts are down
    if len(down) > 0: # hosts are down
        # Check if there are any host in the down-list that hasn't sent an alert
        send_alert=0
        for d in down:
            if down[d].alert_sent == 0:
                down[d].alert_sent = 1
                send_alert=1
            else:
                INFO("Alert already sent for " + down[d].hostname)
        # Only send alert if we have hosts that are down, that have not
        # already got an alert.
        if send_alert:
            alert(down)         
    else: 
        INFO("No new hosts are confirmed down. No need to alarm - yet")
        
    # Relax for a while
    DEBUG("Sleeping for " + str(check_time) + " seconds.")
    sleep(check_time)




