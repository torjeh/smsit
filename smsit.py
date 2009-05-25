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

"""
Configuration: this part should be moved to
a configuration file (e.g. /etc/smsit.conf
"""

# List of hosts that should be checked
hosts = ["pbg4.local", "localhost"]

# Phone number(s)
phone_no = []

# Build dictionary that holds the hosts, and how long they have been down.



for h in hosts:
    print(h)

