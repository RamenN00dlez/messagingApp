#!/usr/bin/python3

import sys
import re
from socket import *

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
#Regular expression to match port number in the range 1024-65353
Port = "^6535[0-3]|653[0-4][0-9]|65[0-2][0-9][0-9]|6[0-4][0-9][0-9][0-9]|5[0-9][0-9][0-9][0-9]|4[0-9][0-9][0-9][0-9]|3[0-9][0-9][0-9][0-9]|2[0-9][0-9][0-9][0-9]|1[0-9][0-9][0-9][0-9]|[2-9][0-9][0-9][0-9]|102[4-9]|10[3-9][0-9]|1[1-9][0-9][0-9]$"

serverip = ""
serverport = ""
username = ""
registered = False

#Verify whether or not a command is valid. True if yes, False if no
def verify_input(cmd):
    cmd = cmd.split(" ")
    cmdc = len(cmd)
    if(cmd[0] == "register" and cmdc == 4):
        if(re.match(IPv4, cmd[2]) != None and re.match(Port, cmd[3])):
            return True
    elif(cmd[0] == "help" and cmdc == 1):
        print("\tregister <contact-name> <IP-address> <port>\n\tcreate <contact-list-name>\n\tquery-lists\n\tjoin <contact-list-name> <contact-name>\n\tleave <contact-list-name> <contact-name>\n\texit <contact-name>\n\tim-start <contact-list-name> <contact-name>\n\tim-complete <contact-list-name> <contact-name>\n\tsave <file-name>\n\tquit")
    elif(cmd[0] == "create" and cmdc == 2):
        return True
    elif(cmd[0] == "query-lists" and cmdc == 1):
        return True
    elif(cmd[0] == "join" and cmdc == 3):
        return True
    elif(cmd[0] == "leave" and cmdc == 3):
        return True
    elif(cmd[0] == "exit" and cmdc == 2):
        return True
    elif(cmd[0] == "im-start" and cmdc == 3):
        return True
    elif(cmd[0] == "im-complete" and cmdc == 3):
        return True
    elif(cmd[0] == "save" and cmdc == 2):
        return True
    elif(cmd[0] == "quit" and cmdc == 1):
        sys.exit()
    return False
    
def main():
    if(len(sys.argv) != 3):
        print("\033[91m[ERROR]\033[0m Must define server ip and port number!\n\t\tFormat: ./client.py <server ip> <server port>")
        sys.exit()
    
    response = ""
    serverip = sys.argv[1]
    serverport = int(sys.argv[2])
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    while(True):
        msg = input("Please enter command.\n> \033[994m")
        if(verify_input(msg)):
            clientSocket.sendto(msg.encode(), (serverip, serverport))
            response, addr = clientSocket.recvfrom(2048)
            print(response.decode())
        else:
            print("Invalid syntax. Command not sent.")


if(__name__ == '__main__'):
    main()
