#!/usr/bin/env python3

from string import Template
from argparse import ArgumentParser
import jinja2
from pathlib import Path

# Preparing arguments
argparser = ArgumentParser(description='Generate config')
argparser.add_argument('-s', '--source', help='path to source file', type=str, required=True)
argparser.add_argument('-i', '--inter', help='check interval, minutes. Default: 100', type=int, default=100)
argparser.add_argument('-l', '--limit', help='limit records from source file', type=int)
args = argparser.parse_args()

# some work variables
workdir = Path(__file__).resolve().parent
template_file_path = workdir / 'haproxy.j2'
output_file_path = workdir / 'haproxy.cfg'

with open(template_file_path, 'rt') as template_file:
    template_obj = Template(template_file.read())

# server_records = list()
proxies = list()
with open(args.source, 'rt') as source_obj:
    for line in source_obj:
        if args.limit is not None and len(proxies) >= args.limit:
            break
        line_s = line.split()
        proxy = line_s[0]
        if len(line_s) > 4:
            weight = int(line_s[4])
        else:
            weight = 1
        proxies.append((proxy, weight))

template = jinja2.Environment(
    loader=jinja2.FileSystemLoader(workdir.as_posix()),
    trim_blocks=True).get_template(f'haproxy.j2')
with open(output_file_path, 'wt') as output_file:
    output_file.write(
        template.render(
            proxies=proxies,
            interval=args.inter
        ))
print(f'Saved {output_file_path}')