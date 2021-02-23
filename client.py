#!/usr/bin/python3

import sys
import re
from socket import *
from multiprocessing import Process, Value, Manager
from time import sleep
import os

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
msgre = "^([0-9]+,[A-Za-z0-9_]+\n((2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9]),(6553[0-4]|655[0-2][0-9]|65[0-4][0-9][0-9]|6[0-4][0-9][0-9][0-9]|[1-5][0-9][0-9][0-9][0-9]|[2-9][0-9][0-9][0-9]|1[1-9][0-9][0-9]|10[3-9][0-9]|102[4-9])\n)+---(\n\033\[34m[A-Za-z0-9_]+\033\[0m> .*)?)"

serverip = ""
serverport = -1
manager = Manager()
d = manager.dict()
myport = Value('i', -1)
reg = Value('i', 0)
clientSocket = None
v = Value('i', -1)
done = Value('i', 1)
rip = Value('i', 0)

#continuously wait for input to a socket.
def recv(fileno):
    #reopen the stdin file descriptor so we can call input in a multithreaded process
    sys.stdin = os.fdopen(fileno)
    global clientSocket, username, v, done, rip, d, myport, reg
    while(True):
        #get the next message
        mesg, clientAddr = clientSocket.recvfrom(2048)
        done.value = 0
        mesg = mesg.decode()
        #check if the message is a p2p IM message
        if(re.match(msgre, mesg) != None):
            #split the header and the contents
            (header, msg) = mesg.split("---")
            lstname = mesg.split("\n")[0].split(',')[1]
            ip = d[1]
            
            #get the destination ip/port and the last contact's ip/port
            head = header.split("\n")
            (hednum, lst) = head[0].split(",")
            hednum = int(hednum)
            (dstip, dstport) = head[hednum].split(",")
            (lastip, lastport) = head[-2].split(",")
            #check if we called the message to start
            if(v.value == 1):
                v.value = -1
                #prompt the user to input a message
                message = input(f"\033[0mPlease enter a message to send to the contact list: \033[1m{lstname}\033[0m\n> \033[36m")
                #send the message to the first client in the list
                header = mesg
                send(header, "\033[34m" + d[2] + ">\033[0m " + message)
            elif(lastip != dstip or lastport != dstport):
                #the message is not at its last hop, print the message and send off the message
                print("\033[0m\n" + '-'*25 + "\nNew incoming message to list \033[1m" + lstname + "\033[0m" + msg + "\033[0m\n" + '-'*25)
                send(header + "---", msg)
                print("\033[0mPlease enter command.\n> \033[36m", end='')
            elif(lastip == dstip and lastport == dstport):
                #the message is at its last hop, we don't need to print because this receiver sent the message first.
                #tell the server that the IM-Session is complete
                fin = "im-complete " + header.split("\n")[0].split(",")[1] + " " + d[2]
                clientSocket.sendto(fin.encode(), (serverip, serverport,))
                m, ca = clientSocket.recvfrom(2048)
                print("\033[35m" + m.decode() + "\033[0m")
                done.value = 1
        else:
            #print the return value from the server
            print("\033[35m\n" + mesg + "\033[0m")
            #check if the user called to exit their client and was successful
            #rip.value=1 triggers the program and its threads to exit
            if(v.value == 3 and mesg == "SUCCESS"):
                rip.value = 1
            #mark processing as complete
            done.value = 1

#forward a message to the next peer in the list
def send(header, msg):
    global clientSocket
    #split up the message header
    head = header.split("\n")
    (hednum, lst) = head[0].split(",")
    #get the index of the next target
    hednum = int(hednum)
    #reconstruct the message header to increment the index
    head[0] = str(hednum + 1) + "," + lst
    #get the destination ip and port
    dest = head[hednum + 1]
    (dstip, dstport) = dest.split(',')
    #reconstruct the message and send it off
    newmsg = '\n'.join(head) + msg
    if(dstip != "---"):
        clientSocket.sendto(newmsg.encode(), (dstip, int(dstport),))


#Verify whether or not a command is valid. True if yes, False if no
def verify_input(cmd):
    global d, myport, reg, clientSocket, rip, done
    cmd = cmd.split(" ")
    cmdc = len(cmd)
    #the user is definitely already registered if they got this far.
    if(cmd[0] == "register" and cmdc == 4):
        print("\033[0mYou are already registered!")
        done.value = 1
        return False
    elif(cmd[0] == "help" and cmdc == 1):
        #output a general help dialog for the user
        print("\033[0m\tregister <contact-name> <IP-address> <port>\n\tcreate <contact-list-name>\n\tquery-lists\n\tjoin <contact-list-name> <contact-name>\n\tleave <contact-list-name> <contact-name>\n\texit <contact-name>\n\tim-start <contact-list-name> <contact-name>\n\tim-complete <contact-list-name> <contact-name>\n\tsave <file-name>")
        done.value = 1
        return False
    elif(cmd[0] == "create" and cmdc == 2):
        #the user wants to create a new contact list
        #check the list name to be alphanumeric (or with underscores)
        if(re.match("^[A-Za-z0-9_]+$", cmd[1]) != None):
            return True
        else:
            print("\033[0mInvalid contact list name.")
            done.value = 1
            return False
    elif(cmd[0] == "query-lists" and cmdc == 1):
        #the user wants to get a list of the contact lists on the serverside
        return True
    elif(cmd[0] == "join" and cmdc == 3):
        #the user wants to join a contact list
        #check if the user has the right name
        if(d[2] == cmd[2]):
            return True
        else:
            print("\033[0mThat's not your username!")
            done.value = 1
            return False
    elif(cmd[0] == "leave" and cmdc == 3):
        #the user wants to leave a list
        #check if the user has the right name
        if(cmd[2] == d[2]):
            return True
        else:
            print("\033[0mThat's not your username!")
            done.value = 1
            return False
    elif(cmd[0] == "exit" and cmdc == 2):
        #the user wants to log off
        #check to make sure the user has the right name
        if(cmd[1] == d[2]):
            return True
        else:
            print("\033[0mThat's not your username!")
            done.value = 1
            return False
    elif(cmd[0] == "im-start" and cmdc == 3):
        #the user wants to start an IM-session
        #check that the user has the right name
        if(cmd[2] == d[2]):
            return True
        else:
            print("\033[0mThat's not your username!")
            done.value = 1
            return False
    elif(cmd[0] == "im-complete" and cmdc == 3):
        #the user wants to complete an IM-session
        #check if the user has the right name
        if(cmd[2] == d[2]):
            return True
        else:
            print("\033[0mThat's not your username!")
            done.value = 1
            return False
    elif(cmd[0] == "save" and cmdc == 2):
        #the user wants to save the current configuration
        #make sure the filename is alphanumeric (with underscores)
        if(re.match("[A-Za-z0-9_]*", cmd[1]) != None):
            return True
        else:
            return False
    else:
        #the command wasn't valid. Tell the user about it
        print("\033[0mInvalid Command.\n\tSee <help> for a list of commands.")
        done.value = 1
    return False

#accept a clientside command to send to the server
def servcmd(fileno):
    global serverip, serverport, clientSocket, v, done
    sys.stdin = os.fdopen(fileno)
    print("Please register first.")
    while(True):
        #if the program is completed with the previous command processing, accept a new command
        if(done.value == 1):
            #prompt the user for a new command and raise the flag that a process is in
            msg = input("Please enter command.\n> \033[36m")
            done.value = 0
            #if the input is valid, raise the right command flag for later interpretation and send the command to the server
            #if it is invalid, mark the processing as complete
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
    global d, clientSocket, serverip, serverport, p, pr, v, done, rip
    #ensure that the user gave a valid number of parameters
    if(len(sys.argv) != 3):
        print("\033[91m[ERROR]\033[0m Must define server ip and port number!\n\t\tFormat: ./client.py <server ip> <server port>")
        sys.exit()
    ##ensure that the user gave a valid IPv4 address and port number
    response = ""
    serverip = sys.argv[1]
    serverport = int(sys.argv[2])
    if(re.match(IPv4, serverip) is None or not (1023 < serverport and serverport < 65535)):
        print("Invalid server IP and/or port number.")
        sys.exit()

    clientSocket = socket(AF_INET, SOCK_DGRAM)
    #require the user to register before performing any other commands
    reg.value = 0
    while(reg.value == 0):
        cmd = input("Please enter your registration information.\n> \033[36m").split(" ")
        cmdc = len(cmd)
        if(cmd[0] == "quit" and cmdc == 1):
            #user wants to quit before registering
            sys.exit()
        elif(cmd[0] == "register" and cmdc == 4):
            #fix the color for normal output for ease of reading
            print("\033[0m", end='')
            #user wants to register
            #check that the user has a valid ip address and port number
            if(re.match(IPv4, cmd[2]) != None and 1023 < int(cmd[3]) and int(cmd[3]) < 65535):
                #check that the user has a valid name
                if(re.match("^[A-Za-z0-9_]+$", cmd[1]) != None):
                    test = 0
                    #test to see if the user's given port is open
                    try:
                        probe = socket(AF_INET,SOCK_DGRAM)
                        probe.bind(('', int(cmd[3])))
                    except Exception as e:
                        #the port is not open
                        probe.close()
                        test = 1
                    if(test == 0):
                        #the port is open, attempt to register with the server
                        reg.value = 1
                        d[2] = cmd[1]
                        d[1] = cmd[2]
                        myport.value = int(cmd[3])
                        probe.sendto((' '.join(cmd)).encode(), (serverip,serverport,))
                        dat, addr = probe.recvfrom(1024)
                        probe.close()
                        if(dat.decode() == "SUCCESS"):
                            #the user has successfully registered
                            print("Successfully registered!")
                            clientSocket.bind(('', myport.value))
                            reg.value = 1
                        else:
                            #the user failed to register
                            print("Failed to register.")
                            reg.value = 0
                            myport.value = -1
                        print(dat.decode())
                    else:
                        print("\033[0mThat port is already taken.")
                else:
                    print("\033[0mInvalid username.")
            else:
                print("\033[0mBad port or IP address.")
        else:
            print("\033[0mYou need to register first. Use the syntax:\nregister <username> <ipv4 address> <port>\nAlternantively, type \"quit\" to quit.")


    #start listening for incoming messages
    p = Process(target=servcmd, args=(sys.stdin.fileno(),))
    p.start()

    #handle client-server messages
    pr = Process(target=recv, args=(sys.stdin.fileno(),))
    pr.start()

    #wait for the program to kill itself
    while(True):
        if(rip.value == 1):
            #the program kill flag has been raised. Terminate threads and exit.
            p.terminate()
            p.join()
            pr.terminate()
            pr.join()
            sys.exit(1)

if(__name__ == '__main__'):
    main()
