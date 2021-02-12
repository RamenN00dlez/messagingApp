#!/usr/bin/python3

import sys
import re
from socket import *
from multiprocessing import Process, Value, Manager
from time import sleep
import os
import ctypes

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
msgre = "([0-9]+,[A-Za-z0-9_]+\n(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9]),(6553[0-4]|655[0-2][0-9]|65[0-4][0-9][0-9]|6[0-4][0-9][0-9][0-9]|[1-5][0-9][0-9][0-9][0-9]|[2-9][0-9][0-9][0-9]|1[1-9][0-9][0-9]|10[3-9][0-9]|102[4-9])\n---\n([A-Za-z0-9_]+> .*)?)"

serverip = ""
serverport = -1
manager = Manager()
d = manager.dict()
myport = Value('i', -1)
registered = False
clientSocket = None
v = Value('i', -1)
done = Value('i', 1)
rip = Value('i', 0)

def recv(fileno):
    sys.stdin = os.fdopen(fileno)
    global clientSocket, username, v, done, rip, d, myport
    while(True):
        mesg, clientAddr = clientSocket.recvfrom(2048)
        done.value = 0
        mesg = mesg.decode()
        if(re.match(msgre, mesg) != None):
            (header, msg) = mesg.split("---")
            lstname = mesg.split("\n")[0].split(',')[1]
            ip = d[1]
            
            head = header.split("\n")
            (hednum, lst) = head[0].split(",")
            hednum = int(hednum)
            dest = head[hednum + 1]
            (dstip, dstport) = dest.split(',')

            if(v.value == 1):
                v.value = -1
                message = input(f"\033[0mPlease enter a message to send to the contact list: \033[1m{lstname}\033[0m\n> \033[36m")
                header = mesg
                send(header, "\033[34m" + d[2] + ">\033[0m " + message)

            if(d[1] != dstip and myport.value != int(dstport)):
                print("\033[0mNew incoming message to list \033[1m" + lstname + "\033[0m\n" + msg + "\033[0m")
                send(header, msg)
                print("Pls enter command.\n> \033[36m", end='')
            else:
                fin = "im-complete " + header.split("\n")[0].split(",")[1] + " " + d[2]
                clientSocket.sendto(fin.encode(), (serverip, serverport,))
        else:
            print("\033[0mServer output:\n" + mesg)
            if(v.value == 2 and mesg == "FAILURE"):
                d[2] = ""
                registered = False
            elif(v.value == 3 and mesg == "SUCCESS"):
                rip.value = 1
        done.value = 1

def send(header, msg):
    global clientSocket
    head = header.split("\n")
    (hednum, lst) = head[0].split(",")
    hednum = int(hednum)
    head[0] = str(hednum + 1) + "," + lst
    dest = head[hednum + 1]
    (dstip, dstport) = dest.split(',')
    newmsg = '\n'.join(head) + msg
    if(dstip != "---"):
        clientSocket.sendto(newmsg.encode(), (dstip, int(dstport),))


#Verify whether or not a command is valid. True if yes, False if no
def verify_input(cmd):
    global d, myport, registered, clientSocket, rip
    cmd = cmd.split(" ")
    cmdc = len(cmd)
    if(cmd[0] == "register" and cmdc == 4):
        if(re.match(IPv4, cmd[2]) != None and 1023 < int(cmd[3]) and int(cmd[3]) < 65535 and not registered and re.match("^[A-Za-z0-9_]+$", cmd[1]) != None):
            registered = True
            d[2] = cmd[1]
            if(myport != -1):
                d[1] = cmd[2]
                myport.value = int(cmd[3])
                clientSocket.bind(('', myport.value))
            return True
        else:
            print("You are already registered!")
            return False
    elif(cmd[0] == "help" and cmdc == 1):
        print("\033[0m\tregister <contact-name> <IP-address> <port>\n\tcreate <contact-list-name>\n\tquery-lists\n\tjoin <contact-list-name> <contact-name>\n\tleave <contact-list-name> <contact-name>\n\texit <contact-name>\n\tim-start <contact-list-name> <contact-name>\n\tim-complete <contact-list-name> <contact-name>\n\tsave <file-name>\n\tquit (only valid if not registered.)")
    elif(cmd[0] == "create" and cmdc == 2 and re.match("^[A-Za-z0-9_]+$", cmd[1]) != None):
        return True
    elif(cmd[0] == "query-lists" and cmdc == 1):
        return True
    elif(cmd[0] == "join" and cmdc == 3 and cmd[2] == d[2]):
        return True
    elif(cmd[0] == "leave" and cmdc == 3 and cmd[2] == d[2]):
        return True
    elif(cmd[0] == "exit" and cmdc == 2 and cmd[1] == d[2]):
        return True
    elif(cmd[0] == "im-start" and cmdc == 3 and cmd[2] == d[2]):
        return True
    elif(cmd[0] == "im-complete" and cmdc == 3 and cmd[2] == d[2]):
        return True
    elif(cmd[0] == "save" and cmdc == 2):
        return True
    elif(cmd[0] == "quit" and cmdc == 1 and d[2] == ""):
        rip.value = 1
    else:
        print("\033[0mInvalid Command.\n\tSee <help> for a list of commands.")
    return False

def servcmd(fileno):
    global serverip, serverport, clientSocket, v, done
    sys.stdin = os.fdopen(fileno)
    print("Please register first.")
    while(True):
        if(done.value == 1):
            msg = input("Please enter command.\n> \033[36m")
            done.value = 0
            if(verify_input(msg)):
                if(msg.split(' ')[0] == 'im-start'):
                    v.value = 1
                elif(msg.split(' ')[0] == 'register'):
                    v.value = 2
                elif(msg.split(' ')[0] == 'exit'):
                    v.value = 3
                else:
                    v.value = -1
                clientSocket.sendto(msg.encode(), (serverip, serverport,))
    
def main():
    global clientSocket, serverip, serverport, p, pr, v, done, rip
    if(len(sys.argv) != 3):
        print("\033[91m[ERROR]\033[0m Must define server ip and port number!\n\t\tFormat: ./client.py <server ip> <server port>")
        sys.exit()
    
    response = ""
    serverip = sys.argv[1]
    serverport = int(sys.argv[2])
    if(re.match(IPv4, serverip) is None or not (1023 < serverport and serverport < 65535)):
        print("Invalid server IP and/or port number.")
        sys.exit()
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    #start listening for incoming messages
    p = Process(target=servcmd, args=(sys.stdin.fileno(),))
    p.start()

    #handle client-server messages
    pr = Process(target=recv, args=(sys.stdin.fileno(),))
    pr.start()

    #wait for the program to kill itself
    while(True):
        if(rip.value == 1):
            p.terminate()
            p.join()
            pr.terminate()
            pr.join()
            sys.exit(1)

if(__name__ == '__main__'):
    main()
