#!/usr/bin/python3

import sys
import os
from datetime import datetime
from socket import *
import re
from multiprocessing import Process

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"

class List:
    def __init__(self, arr):
        self.name = arr[0]
        self.count = int(arr[1])
        self.in_chat = False
        self.initiator = ""
        self.members = []

class Person:
    def __init__(self, data):
        self.name = data[0]
        self.ip = data[1]
        self.port = data[2]

global p
serverIP = ""
serverPort = -1
serverSocket = None
usercount = 0
contact_names = []
listcount = 0
contact_lists = []

#print a server dialog message
def dialog(message):
    print('\033[93m[' + datetime.now().strftime("%H:%M:%S") + "]\033[0m " + message)

#print the current loaded contact configuration
def print_config():
    global contact_names, contact_lists, usercount, listcount
    print("Current Configuration:")
    print("Users (count =", str(usercount) + "):")
    for contact in contact_names:
        print("\t" + contact.name + "," + contact.ip + "," + contact.port)
    print("Contact lists (count =", str(listcount) + "):")
    for lst in contact_lists:
        print("\tNew List: " + lst.name+ "," + str(lst.count))
        for member in lst.members:
            print("\t\t" + member.name + "," + member.ip + "," + member.port)
    print("\n")

#load a passed config file into the contacts. Only meant for startup
def load(filename):
    try:
        dialog("Loading configuration from file: \033[1m" + filename + "\033[0m...")
        f = open(filename, "r")
        global usercount, contact_names, listcount, contact_lists
        usercount = int(f.readline().strip())
        #add each user to the address book
        for i in range(usercount):
            person = Person(f.readline().strip().split(","))
            #If a user's IP is not a valid address, fail.
            if(re.match(IPv4, person.ip) is None or not (1023 < int(person.port) and int(person.port) < 65535)):
                dialog("Failed to load configuration file \033[1m" + filename + "\033[0m.")
                usercount = 0
                listcount = 0
                contact_names = []
                contact_lists = []
                return "FAILURE"
            contact_names.append(person)
        listcount = int(f.readline().strip())
        #add each contact list
        for l in range(listcount):
            lst = List(f.readline().strip().split(","))
            contact_lists.append(lst)
            #add each user in the contact list to the respective list
            for k in range(contact_lists[l].count):
                contact = Person(f.readline().strip().split(","))
                #If a user's IP is not a valid address, fail.
                if(re.match(IPv4, contact.ip) == None or not (1023 < int(contact.port) and int(contact.port) < 65535)):
                    dialog("Failed to load configuration file \033[1m" + filename + "\033[0m.")
                    usercount = 0
                    listcount = 0
                    contact_names = []
                    contact_lists = []
                    return "FAILURE"
                contact_lists[l].members.append(contact)
        f.close()
        dialog("Successfully loaded configuration file \033[1m" + filename + "\033[0m.")
        print_config()
        return "SUCCESS"
    except Exception as ex:
        print("\033[91m[ERROR]\033[0m " + str(ex))
        dialog("Failed to load configuration file \033[1m" + filename + "\033[0m.")
        usercount = 0
        listcount = 0
        contact_names = []
        contact_lists = []
        return "FAILURE"
        
#add a user to the contact list. Failure if the user already exists
def register(name, ip, port):
    dialog("Attempting to add user with details:\n\t\tname = \033[1m" + name + "\033[0m\n\t\tip   = \033[1m" + ip + "\033[0m\n\t\tport = \033[1m" + port + "\033[0m\n")
    if(re.match(IPv4, ip) is None or not (1023 < int(port) and int(port) < 65354)):
        dialog("Failed to add user \033[1m" + name + "\033[0m.")
        return "FAILURE"
    #check the ip/port combo with the server's
    if(ip == serverIP and port == serverPort):
        dialog("Failed to add user \033[1m" + name + "\033[0m.")
        return "FAILURE"
    #check the user info with existing user info for conflicts
    global usercount, contact_names
    for i in range(usercount):
        #check if the username is taken or not.
        if(contact_names[i].name == name or (contact_names[i].ip == ip and contact_names[i].port == port)):
            dialog("Failed to add user \033[1m" + name + "\033[0m.")
            return "FAILURE"
    #the user is not present, add them to the list.
    contact = Person([name, ip, port])
    contact_names.append(contact)
    usercount = usercount + 1
    print_config()
    return "SUCCESS"

#create a new contact list, return failure if the list already exists or number of maximum lists exeeded
def create(list_name):
    dialog("Attempting to create contact list with name = \033[1m" + list_name + "\033[0m.")
    global listcount, contact_lists
    #check if a contact list of the given name exists
    for lst in contact_lists:
        if(lst.name == list_name):
            dialog("Failed to create contact list.")
            return "FAILURE"
    lst = List([list_name, "0"])
    contact_lists.append(lst)
    listcount = listcount + 1
    dialog("Contact list \033[1m" + list_name + "\033[0m successfully created.")
    print_config()
    return "SUCCESS"

#return the contact lists and their members.
def query_lists():
    dialog("Querying contact list.")
    global listcount, contact_lists
    ret = str(listcount) + "\n"
    for lst in contact_lists:
        ret += lst.name + "\n"
    return ret

#add the user with the passed name to the specified contact list
def join(list_name, name):
    dialog("Attempting to add user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
    global usercount, contact_names, listcount, contact_lists
    #if the user is in a chat, they cannot exit.
    for lst in contact_lists:
        if(lst.in_chat):
            for member in lst.members:
                if(member.name == name):
                    dialog("Failed to remove user \033[1m" + name + "\033[0m.")
                    return "FAILURE"
    #find the list, if it doesnt exist, fail.
    for l in range(listcount):
        #list found.
        if(contact_lists[l].name == list_name):
            for contact in contact_names:
                if(contact.name == name):
                    contact_lists[l].members.append(contact)
                    contact_lists[l].count = contact_lists[l].count + 1
                    dialog("Successfully added user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
                    print_config()
                    return "SUCCESS"
    dialog("Failed to add user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
    return "FAILURE"

#remove the user with the given name from the specified list.
def leave(list_name, name):
    dialog("Attempting to remove user \033[1m" + name + "\033[0m from contact list \033[1m" + list_name + "\033[0m.")
    global contact_lists, contact_names
    #if the user is in a chat, they cannot exit.
    for lst in contact_lists:
        if(lst.in_chat):
            for member in lst.members:
                if(member.name == name):
                    dialog("Failed to remove user \033[1m" + name + "\033[0m.")
                    return "FAILURE"
    for l in range(listcount):
        if(contact_lists[l].name == list_name):
            for k in range(contact_lists[l].count):
                if(contact_lists[l].members[k].name == name):
                    del contact_lists[l].members[k]
                    contact_lists[l].count = contact_lists[l].count - 1
                    dialog("Successfully removed user \033[1m" + name + "\033[0m from contact list \033[1m" + list_name + "\033[0m.")
                    print_config()
                    return "SUCCESS"
    dialog("Failed to remove user \033[1m" + name + "\033[0m from contact list \033[1m" + list_name + "\033[0m.")
    return "FAILURE"

#remove a contact name from the active users list and any contact-list they are in
#if the user is in an ongoing IM, they cannot leave until the chat is terminated.
def exit(name):
    global contact_names, contact_lists, usercount, listcount 
    removed = False
    dialog("Attempting to remove user \033[1m" + name + "\033[0m...")
    #if the user is in a chat, they cannot exit.
    for lst in contact_lists:
        if(lst.in_chat):
            for member in lst.members:
                if(member.name == name):
                    dialog("Failed to remove user \033[1m" + name + "\033[0m.")
                    return "FAILURE"
    #remove the user from the contacts list
    for i in range(usercount):
        if(contact_names[i].name == name):
            del contact_names[i]
            usercount = usercount-1
            removed = True
            break
    #remove the user from any contact lists they were in
    for l in range(listcount):
        for k in range(contact_lists[l].count):
            if(contact_lists[l].members[k].name == name):
                del contact_lists[l].members[k]
                contact_lists[l].count = contact_lists[l].count-1
                removed = True
                break
    if(removed):
        print_config()
        dialog("User \033[1m" + name + "\033[0m was successfully removed.")
        return "SUCCESS"
    else:
        dialog("Failed to remove user \033[1m" + name + "\033[0m.")
        return "FAILURE"

#Begin an IM chat session with users in a certain contact list
def im_start(list_name, name):
    global listcount, contact_lists, contact_names, usercount
    dialog("Attempting to start an IM chat session for \033[1m" + list_name + "\033[0m initiated by \033[1m" + name + "\033[0m.")
    pas = False

    #make sure the user exists
    for i in range(usercount):
        if(contact_names[i].name  == name):
            pas = True
            break
    #if the user did not exist, fail.
    if(not pas):
        dialog("Failed to start an IM chat session for \033[1m" + list_name + "\033[0m initiated by \033[1m" + name + "\033[0m.")
        return "FAILURE"

    #make sure the list exists (and if so, that the user is in the list)
    for l in range(listcount):
        if(contact_lists[l].name == list_name):
            for k in range(contact_lists[l].count):
                #found list with passed user - set it to chat mode, give initiator list of users
                if(contact_lists[l].members[k].name == name):
                    contact_lists[l].in_chat = True
                    contact_lists[l].initiator = name
                    code = "0," + contact_lists[l].name + "\n"
                    for user in contact_lists[l].members:
                        if(user.name != name):
                            code += user.ip + "," + user.port + "\n"
                    code += contact_lists[l].members[k].ip + "," + contact_lists[l].members[k].port + "\n---\n"
                    dialog("Successfully started IM chat session for \033[1m" + list_name + "\033[0m initiated by \033[1m" + name + "\033[0m.")
                    return code
    #if the list did not exist, fail
    dialog("Failed to start an IM chat session for \033[1m" + list_name + "\033[0m initiated by \033[1m" + name + "\033[0m.")
    return "FAILURE"
    

#Termainate an IM chat session with users in a certain contact list
def im_complete(list_name, name):
    global listcount, contact_lists
    dialog("Attempting to complete an IM chat session for \033[1m" + list_name + "\033[0m initiated by \033[1m" + name + "\033[0m.")
    #find the specified list
    for l in range(listcount):
        if(list_name == contact_lists[l].name):
            #check if the list is in a chat and the initiator is the same as specified
            if(contact_lists[l].in_chat and contact_lists[l].initiator == name):
                #credentials matched - remove the list from chat mode
                contact_lists[l].in_chat = False
                contact_lists[l].initiator = ""
                dialog("Successfully completed an IM chat session for \033[1m" + list_name + "\033[0m initiated by \033[1m" + name + "\033[0m.")
                return "SUCCESS"
    dialog("Failed to complete an IM chat session for \033[1m" + list_name + "\033[0m initiated by \033[1m" + name + "\033[0m.")
    return "FAILURE"


#save the current config file. return with appropriate response code
def save(filename):
    dialog("Saving configuration to file: \033[1m" + filename + "\033[0m...")
    try:
        f = open(filename, "w")
        global usercount, contact_names, listcount, contact_lists
        f.write(str(usercount) + "\n")
        for contact in contact_names:
            f.write(contact.name + "," + contact.ip + "," + contact.port + "\n")
        f.write(str(listcount) + "\n")
        for lst in contact_lists:
            f.write(lst.name + "," + str(lst.count) + "\n")
            for member in lst.members:
                f.write(member.name + "," + member.ip + "," + member.port + "\n")
        f.close()
        dialog("Configuration sucessfully saved to file \033[1m" + filename + "\033[0m.")
        return "SUCCESS"
    except:
        dialog("Configuration save failed.")
        return "FAILURE"

#validate a command, execute it if valid.
def verify_input(cmd):
    cmd = cmd.split(" ")
    cmdc = len(cmd)
    if(cmd[0] == "quit" and cmdc == 1):
        sure = None
        while(sure != "yes" and sure != "no"):
            sure = input("Are you sure?\nAny unsaved entries will be lost.\nPlease enter 'yes' or 'no'\n> ").lower()
        #cleanly exit the parallel processes
        if(sure == "yes"):
            print("OK... Terminating server...")
            p.terminate()
            p.join()
            sys.exit()
        else:
            print("OK...")

#process a command
def command(cmd):
    if(cmd[0] ==  "register"):
        return register(cmd[1], cmd[2], cmd[3])
    elif(cmd[0] == "create"):
        return create(cmd[1])
    elif(cmd[0] == "query-lists"):
        return query_lists()
    elif(cmd[0] == "join"):
        return join(cmd[1], cmd[2])
    elif(cmd[0] == "leave"):
        return leave(cmd[1], cmd[2])
    elif(cmd[0] == "exit"):
        return exit(cmd[1])
    elif(cmd[0] == "im-start"):
        return im_start(cmd[1], cmd[2])
    elif(cmd[0] == "im-complete"):
        return im_complete(cmd[1], cmd[2])
    elif(cmd[0] == "save"):
        return save(cmd[1])

#continuously check for input
def listen():
    global serverIP, serverPort, serverSocket
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', serverPort))
    dialog("\033[92mServer ready to receive...\033[0m")
    while(True):
        #listen for serverside commands while waiting for socket data
        recv, clientAddr = serverSocket.recvfrom(2048)
        if recv:
            dialog("Message received from: \033[1m" + clientAddr[0] + "\033[0m\n\t\t" + recv.decode())
            response = ""
            cmd = recv.decode().split(" ")
            response = command(cmd)
            serverSocket.sendto(response.encode(), clientAddr)

#start the program here
def main():
    global p, serverPort, serverSocket
    #store the specified port number, if none was given, alert the user and exit the program
    if(len(sys.argv) > 1):
        serverPort = int(sys.argv[1])
        if(not (1023 < serverPort and serverPort < 65535)):
            print("\033[91m[ERROR]\033[0m: Port number must be in the range 1024-65353. Additional restrictions to port range may apply to usage.")
            sys.exit()
    else:
        print("ERROR: Port number must be provided\n[./server.py <port number> (contact list)]\nport number necessary, contact list file is optional.\n")
        sys.exit()

    print("Starting IM Server process on port #" + str(serverPort) + "...")
    #if a contact list file was given, load it.
    if(len(sys.argv) > 2):
        print("Loading contacts from list: " + sys.argv[2] + "...")
        load(sys.argv[2])
    

    #listen for clients
    p = Process(target=listen)
    p.start()

    while(True):
        cmd = input()
        verify_input(cmd)

if(__name__ == '__main__'):
    main()
