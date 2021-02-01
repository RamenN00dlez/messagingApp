#!/usr/bin/python3

import sys
from socket import *

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
#Regular expression to match port number in the range 1024-65353
Port = "^6535[0-3]|653[0-4][0-9]|65[0-2][0-9][0-9]|6[0-4][0-9][0-9][0-9]|5[0-9][0-9][0-9][0-9]|4[0-9][0-9][0-9][0-9]|3[0-9][0-9][0-9][0-9]|2[0-9][0-9][0-9][0-9]|1[0-9][0-9][0-9][0-9]|[2-9][0-9][0-9][0-9]|102[4-9]|10[3-9][0-9]|1[1-9][0-9][0-9]$"

serverip = ""
serverport = ""
username = ""

#Verify whether or not a command is valid. True if yes, False if no
def verify_input(cmd):
    cmd = cmd.split(" ")
    
    return False
    
def main():
    if(len(sys.argv) != 3):
        print("\033[91m[ERROR]\033[0m Must define server ip and port number!\n\t\tFormat: ./client.py <server ip> <server port>")
        sys.exit()
    serverip = sys.argv[1]
    serverport = int(sys.argv[2])
    


if(__name__ == '__main__'):
    main()
