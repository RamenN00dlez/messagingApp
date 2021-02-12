#!/usr/bin/python3

import sys
import re
from socket import *
from multiprocessing import Process
from time import sleep

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
msgre = "^([0-9],[A-Za-z0-9_]+\n((2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9]),((6553[0-4]|655[0-2][0-9]|65[0-4][0-9][0-9]|6[0-4][0-9][0-9][0-9]|[1-5][1-9][1-9][1-9][1-9]|[2-9][1-9][1-9][1-9]|1[1-9][0-9][0-9]|10[3-9][0-9]|102[4-9])\n)+)---\n\033[34m[A-Za-z0-9_]+> .*)$"

serverip = ""
serverport = -1
username = ""
myip = ""
myport = -1
registered = False
clientSocket = None
p = None

def recv():
    global clientSocket
    while(True):
        m = clientSocket.recv(2048).decode()
        print(f"recv(): {m}")
        sleep(0.5)
        if(re.match(msgre, m) != None):
            mesg, clientAddr = clientSocket.recv(2048, MSG_PEEK)
            (header, msg) = mesg.split("---")
            if((myip, myport) != clientAddr):
                print("New incoming message:\n" + msg)
                send(header, msg)
            else:
                fin = "im-complete " + header.split("\n")[0].split(",")[1] + " " + username
                clientSocket.sendto(fin.encode(), (serverip, serverport,))


def send(header, msg):
    global clientSocket
    head = header.split("\n")
    (hednum, lst) = head.split(",")
    hednum = int(hednum)
    head[0] = str(hednum + 1) + "," + lst
    dest = head[hednum + 1]
    (dstip, dstport) = dest.split(',')
    newmsg = '\n'.join(head) + msg
    print(newmsg)
    if(dstip != "---"):
        clientSocket.sendto(newmsg.encode(), (dstip, int(dstport),))


#Verify whether or not a command is valid. True if yes, False if no
def verify_input(cmd):
    global myip, myport, registered, username, clientSocket, p
    cmd = cmd.split(" ")
    cmdc = len(cmd)
    if(cmd[0] == "register" and cmdc == 4):
        if(re.match(IPv4, cmd[2]) != None and 1023 < int(cmd[3]) and int(cmd[3]) < 65535 and not registered and re.match("^[A-Za-z0-9_]+$", cmd[1]) != None):
            registered = True
            username = cmd[1]
            if(myport != -1):
                myip = cmd[2]
                myport = int(cmd[3])
                clientSocket.bind(('', myport))
            return True
        else:
            print("You are already registered!")
            return False
    elif(cmd[0] == "help" and cmdc == 1):
        print("\tregister <contact-name> <IP-address> <port>\n\tcreate <contact-list-name>\n\tquery-lists\n\tjoin <contact-list-name> <contact-name>\n\tleave <contact-list-name> <contact-name>\n\texit <contact-name>\n\tim-start <contact-list-name> <contact-name>\n\tim-complete <contact-list-name> <contact-name>\n\tsave <file-name>\n\tquit (only valid if not registered.)")
    elif(cmd[0] == "create" and cmdc == 2 and re.match("^[A-Za-z0-9_]+$", cmd[1]) != None):
        return True
    elif(cmd[0] == "query-lists" and cmdc == 1):
        return True
    elif(cmd[0] == "join" and cmdc == 3 and cmd[2] == username):
        return True
    elif(cmd[0] == "leave" and cmdc == 3 and cmd[2] == username):
        return True
    elif(cmd[0] == "exit" and cmdc == 2 and cmd[1] == username):
        return True
    elif(cmd[0] == "im-start" and cmdc == 3 and cmd[2] == username):
        return True
    elif(cmd[0] == "im-complete" and cmdc == 3 and cmd[2] == username):
        return True
    elif(cmd[0] == "save" and cmdc == 2):
        return True
    elif(cmd[0] == "quit" and cmdc == 1 and username == ""):
        p.terminate()
        p.join()
        sys.exit(1)
    else:
        print("\033[0mInvalid Command.\n\tSee <help> for a list of commands.")
    return False
    
def main():
    global clientSocket, username
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
    p = Process(target=recv)
    p.start()

    #handle client-server messages
    print("Please register first.")
    while(True):
        msg = input("Please enter command.\n> \033[36m")
        if(verify_input(msg)):
            clientSocket.sendto(msg.encode(), (serverip, serverport))
            response, addr = clientSocket.recv(2048)
            print("\033[0m" + response.decode())
            if(msg.split(' ')[0] == "im-start"):
                message = input(f"Please enter a message to send to the contact list: \033[1m{msg.split(' ')[1]}\033[0m\n> ")
                header = response.decode()
                send(header, "\033[34m" + username + ">\033[0m " + message)
            elif(msg.split(' ')[0] == 'register' and response.decode() == "FAILURE"):
                username = ""
                registered = False
            elif(msg.split(" ")[0] == "exit" and response.decode() == "SUCCESS"):
                p.terminate()
                p.join()
                sys.exit()


if(__name__ == '__main__'):
    main()
