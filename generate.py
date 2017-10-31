#!/usr/local/bin/python3

import os
from string import Template
from argparse import ArgumentParser

# Preparing arguments
argparser = ArgumentParser(description='Generate config')
argparser.add_argument('-s', '--source', help='path to source file', type=str, required=True)
argparser.add_argument('-o', '--output',
                       help='path to source file', type=str, default='collect.cfg')
argparser.add_argument('-i', '--inter', help='check interval, minutes', type=int, default=100)
argparser.add_argument('-l', '--limit', help='limit records from source file', type=int)
args = argparser.parse_args()

# some work variables
workdir = os.path.dirname(os.path.realpath(__file__))
template_file_path = os.path.join(workdir, 'haproxy.template')
output_file_path = os.path.join(workdir, args.output)

with open(template_file_path, 'rt') as template_file:
    template_obj = Template(template_file.read())

server_records = list()
proxies = dict()
with open(args.source, 'r') as source_obj:
    for line in source_obj:
        line_s = line.split()
        proxy = line_s[0]
        if len(line_s) > 4:
            weight = int(line_s[4])
        else:
            weight = 1
        proxies.update({proxy: weight})

counter = 1
for proxy, weight in proxies.items():
    server_records.append('    server proxy-%iw%i %s  check inter %im weight %i' %
                          (counter, weight, proxy, args.inter, weight))
    if args.limit is not None and len(server_records) >= args.limit:
        break
    counter += 1

with open(output_file_path, 'wt') as output_file:
    output_file.write(template_obj.substitute(servers='\n'.join(server_records)))
