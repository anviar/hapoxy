#!/usr/local/bin/python3

import requests
import logging
import os
import random
import re
import sys

logging.basicConfig(
    filename='/var/log/haproxy/check.log',
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)
attempts = 3
proxies = {
    'http': 'socks5://' + os.environ['HAPROXY_SERVER_ADDR'] + ':' + os.environ['HAPROXY_SERVER_PORT'],
    'https': 'socks5://' + os.environ['HAPROXY_SERVER_ADDR'] + ':' + os.environ['HAPROXY_SERVER_PORT']
}

# 'http://ipinfo.io/ip',
# 'http://ifconfig.me/ip',
services = {
            'http://ipv4.icanhazip.com/',
            'http://v4.ident.me/',
            'http://ipecho.net/plain',
            'http://api.ipify.org',
            'http://checkip.amazonaws.com',
            'http://ifconfig.co/ip'
        }
success = False
for try_count in range(1, attempts + 1):
    req_url = random.sample(services, 1)[0]
    # do not try again this service
    services.remove(req_url)
    try:
        request = requests.get(req_url, timeout=5, proxies=proxies)
    except:
        logging.warning(os.environ['HAPROXY_SERVER_NAME'] + ' -> ' + req_url + ' ' + str(sys.exc_info()[0]))
    else:
        success = True
        break
    if len(services) == 0:
        break

if success:
    ipaddress = request.text.strip()
    if not re.match('([0-9]{1,3}.){3}[0-9]{1,3}', ipaddress):
        ipaddress = None
    logging.info(
        os.environ['HAPROXY_SERVER_NAME']
        + ' -> ' + req_url
        + ' (' + str(try_count) + ') '
        + str(ipaddress)
    )
    exit(0)
else:
    logging.error(os.environ['HAPROXY_SERVER_NAME'])
    exit(1)
