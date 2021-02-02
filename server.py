#!/usr/bin/python3

import sys
from datetime import datetime
from socket import *
import re
from multiprocessing import Process

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
#Regular expression to match port number in the range 1024-65353
Port = "^6535[0-3]|653[0-4][0-9]|65[0-2][0-9][0-9]|6[0-4][0-9][0-9][0-9]|5[0-9][0-9][0-9][0-9]|4[0-9][0-9][0-9][0-9]|3[0-9][0-9][0-9][0-9]|2[0-9][0-9][0-9][0-9]|1[0-9][0-9][0-9][0-9]|[2-9][0-9][0-9][0-9]|102[4-9]|10[3-9][0-9]|1[1-9][0-9][0-9]$"
class List:
    def __init__(self, arr):
        self.name = arr[0]
        self.count = arr[1]
        self.in_chat = False
        self.initiator = ""
        self.members = []

class Person:
    def __init__(self, data):
        self.name = data[0]
        self.ip = data[1]
        self.port = data[2]

global p
serverPort = -1
usercount = "0"
contact_names = []
listcount = "0"
contact_lists = []

#print a server dialog message
def dialog(message):
    print('\033[93m[' + datetime.now().strftime("%H:%M:%S") + "]\033[0m " + message)

#print the current loaded contact configuration
def print_config():
    print("Current Configuration:")
    print("Users (count =", usercount + "):")
    for i in range(int(usercount)):
        print("\t" + contact_names[i].name + "," + contact_names[i].ip + "," + contact_names[i].port)
    print("Contact lists (count =", listcount + "):")
    for l in range(int(listcount)):
        print("\tNew List: " + contact_lists[l].name+ "," + contact_lists[l].count)
        for k in range(int(contact_lists[l].count)):
            print("\t\t" + contact_lists[l].members[k].name + "," + contact_lists[l].members[k].ip + "," + contact_lists[l].members[k].port)
    print("\n")

#load a passed config file into the contacts. Only meant for startup
def load(filename):
    try:
        dialog("Loading configuration from file: \033[1m" + filename + "\033[0m...")
        f = open(filename, "r")
        global usercount, contact_names, listcount, contact_lists
        usercount = f.readline().strip()
        #add each user to the address book
        for i in range(int(usercount)):
            person = Person(f.readline().strip().split(","))
            #If a user's IP is not a valid address, fail.
            if(re.match(IPv4, person.ip) == None or re.match(Port, person.port) == None):
                dialog("Failed to load configuration file \033[1m" + filename + "\033[0m.")
                usercount = "0"
                listcount = "0"
                contact_names = []
                contact_lists = []
                return "FAILURE"
            contact_names.append(person)
        listcount = f.readline().strip()
        #add each contact list
        for l in range(int(listcount)):
            lst = List(f.readline().strip().split(","))
            contact_lists.append(lst)
            #add each user in the contact list to the respective list
            for k in range(int(contact_lists[l].count)):
                contact = Person(f.readline().strip().split(","))
                #If a user's IP is not a valid address, fail.
                if(re.match(IPv4, contact.ip) == None or re.match(Port, contact.port) == None):
                    dialog("Failed to load configuration file \033[1m" + filename + "\033[0m.")
                    usercount = "0"
                    listcount = "0"
                    contact_names = []
                    contact_lists = []
                    return "FAILURE"
                contact_lists[l].members.append(contact)
        f.close()
        dialog("Successfully loaded configuration file \033[1m" + filename + "\033[0m.")
        return "SUCCESS"
    except:
        dialog("Failed to load configuration file \033[1m" + filename + "\033[0m.")
        usercount = "0"
        listcount = "0"
        contact_names = []
        contact_lists = []
        return "FAILURE"
        
    #check if the user is already in the list, if they do, fail.
    for k in range(int(lst.count)):
        if(lst.members[k].name == name):
            dialog("Failed to add user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
            return "FAILURE"
    #find the user in the contact list, succeed if found (and added)
    for i in range(int(usercount)):
        if(contact_names[i].name == name):
            lst.members.append(contact_names[i])
            lst.count = str(int(lst.count) + 1)
            return "SUCCESS"
    dialog("Failed to add user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
    return "FAILURE"



#add a user to the contact list. Failure if the user already exists
def register(name, ip, port):
    dialog("Attempting to add user with details:\n\t\tname = \033[1m" + name + "\033[0m\n\t\tip   = \033[1m" + ip + "\033[0m\n\t\tport = \033[1m" + port + "\033[0m\n")
    if(re.match(IPv4, ip) == None or re.match(Port, port) == None):
        dialog("Failed to add user \033[1m" + name + "\033[0m.")
        return "FAILURE"
    global usercount, contact_names
    for i in range(int(usercount)):
        #check if the username is taken or not.
        if(contact_names[i].name == name or (contact_names[i].ip == ip and contact_names[i].port == port)):
            dialog("Failed to add user \033[1m" + name + "\033[0m.")
            return "FAILURE"
    #the user is not present, add them to the list.
    contact = Person([name, ip, port])
    contact_names.append(contact)
    usercount = str(int(usercount) + 1)
    print_config()
    return "SUCCESS"

#create a new contact list, return failure if the list already exists or number of maximum lists exeeded
def create(list_name):
    dialog("Attempting to create contact list with name = \033[1m" + list_name + "\033[0m.")
    global listcount, contact_lists
    #check if a contact list of the given name exists
    for i in range(int(listcount)):
        if(contact_lists[i].name == list_name):
            dialog("Failed to create contact list.")
            return "FAILURE"
    lst = List([list_name, "0"])
    contact_lists.append(lst)
    listcount = str(int(listcount) + 1)
    dialog("Contact list \033[1m" + list_name + "\033[0m successfully created.")
    return "SUCCESS"

#return the contact lists and their members.
def query_lists():
    dialog("Querying contact list.")
    global listcount, contact_lists
    ret = listcount + "\n"
    for lst in contact_lists:
        ret += lst.name + ", " + lst.count + "\n"
        for member in lst.members:
            ret += member.name + "\n"
    return ret

#add the user with the passed name to the specified contact list
def join(list_name, name):
    dialog("Attempting to add user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
    #if the user is in a chat, they cannot exit.
    for lst in contact_lists:
        if(lst.in_chat):
            for member in lst.members:
                if(member.name == name):
                    dialog("Failed to remove user \033[1m" + name + "\033[0m.")
                    return "FAILURE"
    global usercount, contact_names, listcount, contact_lists
    lst = None
    #find the list, if it doesnt exist, fail.
    for l in range(int(listcount)):
        if(contact_lists[l].name == list_name):
            lst = contact_lists[l]
            break
    if(lst != None):
        for contact in contact_names:
            if(contact.name == name):
                lst.members.append(contact)
                lst.count = str(int(lst.count) + 1)
                dialog("Successfully added user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
                return "SUCCESS"
    dialog("Failed to add user \033[1m" + name + "\033[0m to list \033[1m" + list_name + "\033[0m.")
    return "FAILURE"

#remove the user with the given name from the specified list.
def leave(list_name, name):
    dialog("Attempting to remove user \033[1m" + name + "\033[0m from contact list \033[1m" + list_name + "\033[0m.")
    #if the user is in a chat, they cannot exit.
    for lst in contact_lists:
        if(lst.in_chat):
            for member in lst.members:
                if(member.name == name):
                    dialog("Failed to remove user \033[1m" + name + "\033[0m.")
                    return "FAILURE"
    global contact_lists
    for lst in contact_lists:
        if(lst.name == list_name):
            for k in range(int(lst.members)):
                if(lst.members[k].name == name):
                    del contact_lists[k]
                    dialog("Successfully removed user \033[1m" + name + "\033[0m from contact list \033[1m" + list_name + "\033[0m.")
                    return "SUCCESS"
    dialog("Failed to remove user \033[1m" + name + "\033[0m from contact list \033[1m" + list_name + "\033[0m.")
    return "FAILURE"

#remove a contact name from the active users list and any contact-list they are in
#if the user is in an ongoing IM, they cannot leave until the chat is terminated.
def exit(name):
    global contact_names, contact_lists 
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
    for contact in contact_names:
        if(contact.name == name):
            del contact
            usercount = str(int(usercount)-1)
            removed = True
            break
    #remove the user from any contact lists they were in
    for lst in contact_lists:
        for member in lst.members:
            if(member.name == name):
                del member
                lst.count = str(int(lst.count)-1)
                removed = True
                break
    if(removed):
        dialog("User \033[1m" + name + "\033[0m was successfully removed.")
        return "SUCCESS"
    else:
        dialog("Failed to remove user \033[1m" + name + "\033[0m.")
        return "FAILURE"

#Begin an IM chat session with users in a certain contact list
def im_start(list_name, name):
    dialog("Attempting to start an IM chat session for \033[1m" + list_name"\033[0m initiated by \033[1m" + name + "\033[0m.")

#Termainate an IM chat session with users in a certain contact list
def im_complete(list_name, name):
    dialog("Attempting to start an IM chat session for \033[1m" + list_name"\033[0m initiated by \033[1m" + name + "\033[0m.")

#save the current config file. return with appropriate response code
def save(filename):
    dialog("Saving configuration to file: \033[1m" + filename + "\033[0m...")
    try:
        f = open(filename, "w")
        global usercount, contact_names, listcount, contact_lists
        f.write(usercount + "\n")
        for i in range(int(usercount)):
            f.write(contact_names[i].name + "," + contact_names[i].ip + "," + contact_names[i].port + "\n")
        f.write(listcount + "\n")
        for l in range(int(listcount)):
            f.write(contact_lists[l].name + "," + contact_lists[l].count + "\n")
            for k in range(int(contact_lists[l].count)):
                f.write(contact_lists[l].members[k].name + "," + contact_lists[l].members[k].ip + "," + contact_lists[l].members[k].port + "\n")
        f.close()
        dialog("Configuration sucessfully saved to file \033[1m" + filename + "\033[0m.")
        return "SUCCESS"
    except:
        dialog("Configuration save failed.")
        return "FAILURE"

#validate a command, execute it if valid.
def verify_input(cmd):
    dialog("Executing serverside command...")
    cmd = cmd.split(" ")
    cmdc = len(cmd)
    if(cmd[0] == "register" and cmdc == 4):
        if(re.match(IPv4, cmd[2]) != None and re.match(Port, cmd[3])):
            register(cmd[1], cmd[2], cmd[3])
    elif(cmd[0] == "help" and cmdc == 1):
        print("\tregister <contact-name> <IP-address> <port>\n\tcreate <contact-list-name>\n\tquery-lists\n\tjoin <contact-list-name> <contact-name>\n\tleave <contact-list-name> <contact-name>\n\texit <contact-name>\n\tprint-config\n\tsave <file-name>\n\tquit")
    elif(cmd[0] == "create" and cmdc == 2):
        create(cmd[1])
    elif(cmd[0] == "query-lists" and cmdc == 1):
        print(query_lists())
    elif(cmd[0] == "join" and cmdc == 3):
        join(cmd[1], cmd[2])
    elif(cmd[0] == "leave" and cmdc == 3):
        leave(cmd[1], cmd[2])
    elif(cmd[0] == "exit" and cmdc == 2):
        exit(cmd[1])
    elif(cmd[0] == "save" and cmdc == 2):
        save(cmd[1])
    elif(cmd[0] == "print-config" and cmdc == 1):
        print_config()
    elif(cmd[0] == "quit" and cmdc == 1):
        sure = None
        while(sure != "yes" and sure != "no"):
            if(sure != None):
                print("Please enter 'yes' or 'no'")
            sure = input("Are you sure?\nAny unsaved entries will be lost.\n> ").lower()
        #cleanly exit the parallel processes
        if(sure == "yes"):
            global p
            p.terminate()
            p.join()
            sys.exit()
    return "Invalid command. Type 'help' for help."

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
def listen(serverPort):
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', serverPort))
    dialog("\033[92mServer ready to receive...\033[0m")
    while(True):
        recv, clientAddr = serverSocket.recvfrom(2048)
        if recv:
            dialog("Message received from: \033[1m" + clientAddr[0] + "\033[0m\n\t\t" + recv.decode())
            response = ""
            cmd = recv.decode().split(" ")
            command(cmd)
            serverSocket.sendto(response.encode(), clientAddr)

#start the program here
def main():
    global p
    #store the specified port number, if none was given, alert the user and exit the program
    if(len(sys.argv) > 1):
        serverPort = int(sys.argv[1])
        if(re.match(Port, str(serverPort)) == None):
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
    p = Process(target=listen, args=(serverPort,))
    p.start()

    #listen for serverside commands
    while(True):
        cmd = input()
        verify_input(cmd)
    
if(__name__ == '__main__'):
    main()
