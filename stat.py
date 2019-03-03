#!/usr/bin/env python3

import socket
from configparser import ConfigParser
import os
from time import time
from pathlib import Path
from urllib.request import urlopen
import csv

workdir = Path(__file__).resolve().parent
config = ConfigParser()
config.read(workdir / 'haproxy-tools.cfg')
timestamp = int(time())
pidfile = workdir / 'haproxy-stat.pid'


# check what instance for this TLD not running on same host
def check_pid(pid):
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    else:
        return True


if os.path.isfile(pidfile):
    with open(pidfile, 'r') as pidfile_obj:
        last_pid = pidfile_obj.read()
    if check_pid(last_pid):
        print("Already running: " + pidfile)
        exit(1)
    else:
        with open(pidfile, 'w') as pidfile_obj:
            pidfile_obj.write(str(os.getpid()))
else:
    with open(pidfile, 'w') as pidfile_obj:
        pidfile_obj.write(str(os.getpid()))

# read data from haproxy
with urlopen(config['haproxy']['url'], timeout=10) as stat_req:
    s_lines = list()
    for l in stat_req:
        s_lines.append(l.decode('ASCII').strip('# '))
    csv_obj = csv.DictReader(s_lines, delimiter=',')
    data = [line for line in csv_obj]

proxy_up = 0
proxy_down = 0
for item in data:
    if item['pxname'] == 'proxy':
        if item['status'].startswith('UP'):
            proxy_up += 1
        elif item['status'].startswith('DOWN'):
            proxy_down += 1


def get_general(g_item: str):
    for i in data:
        if i['pxname'] == 'stats' and i['svname'] == 'FRONTEND':
            return i[g_item]
    return 0


graphite_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_graphite(item, value):
    graphite_message = '%s %s %i\n' % (
        config['graphite']['prefix'] + item,
        str(value),
        timestamp)
    graphite_sock.sendto(
        graphite_message.encode(),
        (
            config['graphite']['host'],
            int(config['graphite']['port'])
        )
    )


for item in config['graphite']['general_values'].split(','):
    send_graphite(item, get_general(item))
send_graphite('proxies.up', proxy_up)
send_graphite('proxies.down', proxy_down)

lastsess = list()
for i in data:
    if i['pxname'] == 'proxy' and i['status'] == 'UP' and int(i['lastsess']) > 0:
        lastsess.append(int(i['lastsess']))
if len(lastsess) > 1:
    send_graphite('lastsess.min', min(lastsess))
    send_graphite('lastsess.max', max(lastsess))
    send_graphite('lastsess.avg', sum(lastsess) // len(lastsess))

graphite_sock.close()
pidfile.unlink()
