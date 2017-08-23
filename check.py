#!/usr/local/bin/python3

import os
import random
import requests
import configparser
import re
import logging

workdir = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(workdir, 'haproxy-tools.cfg'))

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
proxies = {
    'http': 'socks5://' + os.environ['HAPROXY_SERVER_ADDR'] + ':' + os.environ['HAPROXY_SERVER_PORT'],
    'https': 'socks5://' + os.environ['HAPROXY_SERVER_ADDR'] + ':' + os.environ['HAPROXY_SERVER_PORT']
}

logging.basicConfig(
    filename=config['check']['log'],
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)


success = False
for try_count in range(1, int(config['check']['attempts']) + 1):
    req_url = random.sample(services, 1)[0]
    # do not try again this service
    services.remove(req_url)
    try:
        request = requests.get(req_url, timeout=int(config['check']['timeout']), proxies=proxies)
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
