#!/usr/local/bin/python3

import socket
import six
import configparser
import os
import time

workdir = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(workdir, 'haproxy-tools.cfg'))
timestamp = int(time.time())
pidfile = os.path.join(workdir, 'haproxy-stat.pid')

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
haproxy_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
haproxy_socket.connect(config['haproxy']['socket'])
haproxy_socket.send(six.b('show stat' + '\n'))
file_handle = haproxy_socket.makefile()
data = file_handle.read().splitlines()
haproxy_socket.close()


def parse_stat_table(line) -> list:
    return line.strip('#').strip().strip(',').split(',')

head = parse_stat_table(data[0])
parsed_table = dict()
for line in data[1:]:
    line_split = parse_stat_table(line)
    if len(line_split) == 1:
        continue
    if line_split[0] not in parsed_table:
        parsed_table.update({line_split[0]: {}})
    if line_split[1] not in parsed_table[line_split[0]]:
        parsed_table[line_split[0]].update({line_split[1]: {}})
    f_indx = 2
    for field in list(line_split[f_indx:]):
        try:
            f_value = int(line_split[f_indx])
        except ValueError:
            f_value = line_split[f_indx]
        if not f_value == '':
            parsed_table[line_split[0]][line_split[1]].update({head[f_indx]: f_value})
        f_indx += 1

# send data to graphite
for item in config['graphite']['general_values'].split(','):
    graphite_message = '%s %s %i' % (
        config['graphite']['prefix'] + item,
        str(parsed_table['main']['FRONTEND'][item]),
        timestamp)

proxy_up = 0
proxy_down = 0
for proxy in parsed_table['proxy']:
    if 'addr' in parsed_table['proxy'][proxy]:
        if parsed_table['proxy'][proxy]['status'].startswith('UP'):
            proxy_up += 1
        elif parsed_table['proxy'][proxy]['status'].startswith('DOWN'):
            proxy_down += 1

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
    send_graphite(item, parsed_table['main']['FRONTEND'][item])
send_graphite('proxies.up', proxy_up)
send_graphite('proxies.down', proxy_down)

graphite_sock.close()
os.remove(pidfile)
