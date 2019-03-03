#!/usr/bin/python3

import os
import random
import requests
import re
import logging
from sys import exc_info

attempts = 3
timeout = 5

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

proxy_url = 'socks5://{}:{}'.format(os.environ['HAPROXY_SERVER_ADDR'], os.environ['HAPROXY_SERVER_PORT'])
proxies = {'http': proxy_url, 'https': proxy_url}

logging.basicConfig(
    format='%(asctime)s [check:%(levelname)s] %(message)s',
    level=logging.INFO
)


success = False
for try_count in range(attempts):
    req_url = random.sample(services, 1)[0]
    # do not try again this service
    services.remove(req_url)
    try:
        request = requests.get(req_url, timeout=timeout, proxies=proxies)
    except Exception as e:
        logging.warning(os.environ['HAPROXY_SERVER_NAME'] + ' -> ' + req_url + ' ' + str(exc_info()[0]))
    else:
        if request.status_code < 300:
            success = True
            break
    if len(services) == 0:
        break

if success:
    ipaddress = request.text.strip()
    if not re.match('([0-9]{1,3}.){3}[0-9]{1,3}', ipaddress):
        ipaddress = None
    logging.debug(ipaddress)
    exit(0)
else:
    logging.error(os.environ['HAPROXY_SERVER_NAME'])
    exit(1)
