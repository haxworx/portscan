#!/usr/bin/env python3

import sys
import socket
import select
import re
import time

class PortScanner:
    def __init__(self, host):
        self.services = False
        self.host = host;
        self.ports = []
        self.ports_count = 0
        self.attempted = 0
        self.results = []

    def set_host(host):
        self.host = host

    def enable_services(self, enabled):
        self.services = enabled

    def port_range(self):
        if not self.services:
            for port in range(1, 2000):
                self.ports.append({ "port": port, "open": False, "seen": False })
        else:
            with open("/etc/services", "r") as f:
                services = re.findall("(.*?)\s+(\d+)\/tcp", f.read())
                for service in services:
                    if len(service) == 2:
                        self.ports.append({"port": int(service[1]), "open": False, "seen": False, 'service': service[0] })
        self.ports_count = len(self.ports)

    def connect(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        try:
            sock.connect((self.host, port['port']))
        except BlockingIOError:
            pass
        except OSError as e:
            print("Error: {}. Try increasing rlimit n files (ulimit -n)." . format(e))
            sys.exit(1)
        return sock

    def scan(self):
        self.port_range()

        poller = select.poll()
        for port in self.ports:
            sock = self.connect(port)
            if sock is not None:
                port['sock'] = sock
                poller.register(sock, select.POLLIN | select.POLLOUT)

        while True:
            events = poller.poll(1000)
            if len(events) == 0:
                break
            for fileno, ev in events:
                # POLLIN, POLLOUT or both POLLIN and POLLOUT.
                if ev == select.POLLIN or ev == select.POLLOUT or (ev == (select.POLLIN | select.POLLOUT)):
                    for port in self.ports:
                        if port['sock'].fileno() == fileno:
                            port['open'] = True
                            poller.unregister(fileno)
                else:
                    poller.unregister(fileno)

        for port in self.ports:
            port['sock'].close()
            if port['open']:
                print("Connected on port: {:>8}" . format(port['port']), end='')
                if 'service' in port:
                    print(" ({})" . format(port['service']), end='')
                print()


def main(host):
    scanner = PortScanner(sys.argv[1])
    scanner.enable_services(True)
    scanner.scan()

def usage():
    print("Usage: {} <host>" . format(sys.argv[0]))
    sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    main(sys.argv[1])
