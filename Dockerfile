FROM haproxy:1.8-alpine
RUN apk add --update python3
COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
COPY check.py /usr/local/bin/check.py
RUN pip3 install requests[socks]
LABEL description="collect haproxy"