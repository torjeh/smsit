#!/usr/bin/python

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
from time import strftime, localtime, sleep, ctime, time
import sys  
import signal # should catch signals to die gracefully
import ConfigParser # ...  import ConfigParser # Read config file



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
def createDaemon(redirect=None):
    UMASK = 0
    WORKDIR = "/"
    MAXFD = 1024

    if redirect:
        REDIRECT_TO=redirect
        # Truncate the file
        open(redirect,"w")
    elif (hasattr(os, "devnull")):
        REDIRECT_TO = os.devnull
    else:
        REDIRECT_TO = "/dev/null"
    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)
 
    if (pid == 0):	# The first child.
        os.setsid()
        try:
            pid = os.fork()	# Fork a second child.
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if (pid == 0):	# The second child.
            os.chdir(WORKDIR)
            os.umask(UMASK)
        else:
            os._exit(0)	# Exit parent (the first child) of the second child.
    else:
        os._exit(0)	# Exit parent of the first child.

    import resource		# Resource usage information.
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
       maxfd = MAXFD
    for fd in range(0, maxfd):
       try:
          os.close(fd)
       except OSError:	# ERROR, fd wasn't open to begin with (ignored)
          pass
    os.open(REDIRECT_TO, os.O_RDWR)	# standard input (0)
    os.dup2(0, 1)			# standard output (1)
    os.dup2(0, 2)			# standard error (2)

    return(0)


def print_hosts(hosts):
    s="Hosts:"
    for h in hosts:
        s+=" "+h
    INFO(s)

# Write the pid to the pidfile.
# We don't care if the file exists,
# or if there is anything in it.
# Just giving a warning ... 
def write_pid_to_file(pidfile):
    # Check if we already have a pidfile
    try: 
        fd=open(pidfile,"ro")
        WARNING("There is already a pid-file.")
        fd.close()
    except:
        fd.close()

    # Now truncate the file and write the pid
    fd=open(pidfile,"w")
    fd.write(str(os.getpid()))
    fd.close()

# This function handles all incoming signals
# (Pretty much just to shut down)
# http://docs.python.org/library/signal.html
def signal_handler(signum, frame):
    INFO("Got signal: " + str(signum) + ". Shutting down. Bye!") 
    # Delete the pid-file

    # Close the logger
    lf.close()
    sys.exit()

# Return a string representation of the current local time.
# E.g. May 31 18:23:19
# We use this when writing to our log-file
def now():
    return str(strftime("%b %d %H:%M:%S ", localtime()))


# Logging functions. If we are not running as a 
# daemon, I guess we should use print instead of write.
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

# Register signal handler for signals:
# SIGTERM 15
# SIGINT CTRL-C
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM,signal_handler)

# List of hosts that should be checked
# Index is the ip-address of the host
hosts = {}

# Read config file
# ConfigParser is included in python and
# documented here http://www.python.org/doc/2.6.2/library/configparser.html
config = ConfigParser.ConfigParser()
config.read("/etc/smsit.conf") # Hardcoded config file ... 
    
# Get global variables from config file
alert_treshold = int(config.get('global','alert_treshold')) # int
check_time = int(config.get('global','check_time')) # int
debug = int(config.get('global','debug')) # int
phone_no=config.get('global','phone_numbers').split(",") # Comma-separated list
daemon=int(config.get('global','daemon')) # int
#gnokiiconfig=config.get('global','gnokiiconfig') # str
logfile=config.get('global','logfile') # str
pidfile=config.get('global','pidfile') # str

# Get hosts from the config file
hostlist=config.items('hosts')
for h in hostlist:
    hosts[h[0]] = host_object(h[0],h[1])

# Go into daemonized form
# Also means write output to a logfile
# and write our pid to the pidfile
if daemon:
    print("Becoming a daemon ...")
    createDaemon("/tmp/smsit.out")
    # Open log-file (in appending mode)
    lf=open(logfile,'a') 
    # Write our pid to pid-file
    write_pid_to_file(pidfile)  
    DEBUG("Redirecting output to /tmp/smsit.out instead of /dev/null to simplify debugging")
else:
    print("Not running as a daemon ...")
   
INFO("SMSit started " + ctime())

# Some sanity checks for the variables read from config file
if alert_treshold < 1:
    WARNING("Alert treshold cannot be 0. Setting it to 1")
    alert_treshold = 1
if check_time < 0:
    WARNING("Check time (the time to sleep between chekcs) needs to be a non-negative number. Setting it to 0.")
    check_time=0
if len(phone_no) is 0:
    WARNING("No phone numbers are specified.")




DEBUG("================================================================")
DEBUG("Configuration")
INFO("________________________________________________________________")
DEBUG("alert_treshold: " + str(alert_treshold))
DEBUG("check_time:     " + str(check_time))
DEBUG("debug:          " + str(debug))
DEBUG("phone_no:       " + str(phone_no))
DEBUG("daemon:         " + str(daemon))
#DEBUG("gnokiiconfig:   " + str(gnokiiconfig))
DEBUG("logfile:        " + str(logfile))
DEBUG("pidfile:        " + str(pidfile))
DEBUG("workingdir:     " + str(os.getcwd()))
DEBUG("My pid:         " + str(os.getpid()))
DEBUG("________________________________________________________________")
""" Body """


# This method is (pretty much) stolen from 
# http://www.wellho.net/solutions/python-python-threads-a-first-example.html
def test_ping_hosts(hosts):
    INFO("================================================================")
    INFO("ip                  alias                Response            ")
    INFO("________________________________________________________________")

    t0 = time()
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
                ipstr = h+" "*(20-len(h)) # ip-address
                astr  = hosts[h].hostname+" "*(20-len(hosts[h].hostname)) # alias
                chck_str = str(hosts[h].checks_failed)+" "*(2-len(str(hosts[h].checks_failed))) # ping-response
                report_str = report[int(igot[0])]+" "*(20-len(report[int(igot[0])])) # Number of failed pings
                INFO(ipstr + astr + " " + report_str + " " + chck_str)
                # Host is down
                if int(igot[0]) == 0: 
                    hosts[h].checks_failed += 1
                # Host is up
                else: 
                    hosts[h].checks_failed = 0
                    hosts[h].alert_sent = 0
            #else: print "No igot ..."
    time_taken=time()-t0
    DEBUG("Spent about " + str(int(time_taken)) + " seconds pinging hosts.")
    INFO("________________________________________________________________")

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

def get_real_exit_code(rv):
    return (rv >> 8) & 0xFF

# send_sms takes care that
# the message is sent to all that are supposed to get it
def send_sms(msg, phone_numbers):
    # Check the length of the message (sms is small - like twitter!)
    if len(msg) > 160:
        WARNING("Message quite long")

    # Do the message pass to alle phonenumbers in list
    # example: echo "hi there" | gnokii --config /etc/gnokiirc --sendsm 12345678
    for p in phone_numbers:
#rv = os.system("echo \""+msg+"\" | gnokii --config " + gnokiiconfig +" --sendsms "+str(p))
        rv = os.system("echo \""+msg+"\" | gnokii --sendsms "+str(p))
        rv = get_real_exit_code(rv)
        if rv:
            WARNING("Could not send SMS: " + str(rv) + ", but don't know what to do about it.")
        sleep(2) # sleep some, to make sure we don't overload the phone and make everything crash ... 

"""
Loop forever (Or until CTRL-C hopefully)
"""
while 1:
    time_to_check_hosts=test_ping_hosts(hosts)
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




