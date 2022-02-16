#!/usr/bin/env python3

import sys
import socket
import re
from multiprocessing import Pool, cpu_count
from concurrent.futures import ThreadPoolExecutor

class PortScanner:
    def __init__(self, host):
        self.services = False
        self.host = host;
        self.ports = []
        self.ports_count = 0
        self.attempted = 0
        self.results = []
        self.cpu_count = cpu_count() or 1

    def set_host(host):
        self.host = host

    def enable_services(self, enabled):
        self.services = enabled

    def port_range(self):
        if not self.services:
            for port in range(1, 65536):
                self.ports.append({ "port": port, "open": False, "seen": False })
        else:
            with open("/etc/services", "r") as f:
                services = re.findall("(.*?)\s+(\d+)\/tcp", f.read())
                for service in services:
                    if len(service) == 2:
                        self.ports.append({"port": int(service[1]), "open": False, "seen": False, 'service': service[0] })
        self.ports_count = len(self.ports)

    def connect(self, port):
        port['seen'] = True
        self.attempted += 1
        print("\r{}%" . format(round((self.attempted / self.ports_count) * 100.0)), end='')
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, port['port']))
        except socket.error as msg:
            return False
        else:
            sock.close()
            port['open'] = True
            return True

    def scan(self):
        self.port_range()
        with ThreadPoolExecutor(max_workers=self.cpu_count) as executor:
            executor.map(self.connect, self.ports)

        print("\r", end='')

        for port in self.ports:
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
