#!/usr/bin/python3

import sys
from datetime import datetime
import time
import re

#regular expression to match an IPv4 address
IPv4 = "^(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(2[0-5][0-5]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
#Regular expression to match port number in the range 1024-65353
Port = "^6535[0-3]|653[0-4][0-9]|65[0-2][0-9][0-9]|6[0-4][0-9][0-9][0-9]|5[0-9][0-9][0-9][0-9]|4[0-9][0-9][0-9][0-9]|3[0-9][0-9][0-9][0-9]|2[0-9][0-9][0-9][0-9]|1[0-9][0-9][0-9][0-9]|[2-9][0-9][0-9][0-9]|102[4-9]|10[3-9][0-9]|1[1-9][0-9][0-9]$"
class List:
    def __init__(self, arr):
        self.name = arr[0]
        self.count = arr[1]
        self.members = []

class Person:
    def __init__(self, data):
        self.name = data[0]
        self.ip = data[1]
        self.port = data[2]

serverPort = -1
#name, list-name,
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
        return True
    except:
        dialog("Configuration save failed.")
        return False

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
                return False
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
                    return False
                contact_lists[l].members.append(contact)
        f.close()
        dialog("Successfully loaded configuration file \033[1m" + filename + "\033[0m.")
        return True
    except:
        dialog("Failed to load configuration file \033[1m" + filename + "\033[0m.")
        usercount = "0"
        listcount = "0"
        contact_names = []
        contact_lists = []
        return False

#add a user to the contact list. Failure if the user already exists
def register(name, ip, port):
    dialog("Attempting to add user with details:\n\t\tname = \033[1m" + name + "\033[0m\n\t\tip   = \033[1m" + ip + "\033[0m\n\t\tport = \033[1m" + port + "\033[0m\n")
    if(re.match(IPv4, ip) == None or re.match(Port, port) == None):
        dialog("Failed to add user \033[1m" + name + "\033[0m.")
        return False
    global usercount, contact_names
    for i in range(int(usercount)):
        #check if the username is taken or not.
        if(contact_names[i].name == name or (contact_names[i].ip == ip and contact_names[i].port == port)):
            dialog("Failed to add user \033[1m" + name + "\033[0m.")
            return False
    #the user is not present, add them to the list.
    contact = Person([name, ip, port])
    contact_names.append(contact)
    usercount = str(int(usercount) + 1)
    print_config()
    return True

#create a new contact list, return failure if the list already exists or number of maximum lists exeeded
def create(list_name):
    dialog("Attempting to create contact list with name = \033[1m" + list_name + "\033[0m.")
    global listcount, contact_lists
    #check if a contact list of the given name exists
    for i in range(int(listcount)):
        if(contact_lists[i].name == list_name):
            dialog("Failed to create contact list.")
            return False
    lst = List([list_name, "0"])
    contact_lists.append(lst)
    listcount = str(int(listcount) + 1)
    dialog("Contact list \033[1m" + list_name + "\033[0m successfully created.")
    return True

#remove a contact name from the active users list and any contact-list they are in
#TODO: check if user is in an ongoing IM. return failure if they are.
def exit(name):
    global usercount, listcount, contact_names, contact_lists 
    tmpusrct = usercount
    tmplstct = listcount
    try:
        dialog("Attempting to remove user \033[1m" + name + "\033[0m...")
        #remove the user from the contacts list
        for i in range(int(usercount)):
            if(contact_names[i].name == name):
                del contact_names[i]
                usercount = str(int(usercount)-1)
                break
        #remove the user fromo any contact lists they were in
        for l in range(int(listcount)):
            for k in range(int(contact_lists[l].count)):
                if(contact_lists[l].members[k].name == name):
                    del (contact_lists[l].members[k])
                    contact_lists[l].count = str(int(contact_lists[l].count)-1)
                    break
        dialog("User \033[1m" + name + "\033[0m was successfully removed.")
        return True
    except:
        usercount = tmpusrct
        listcount = tmplstct
        dialog("Failed to remove user \033[1m" + name + "\033[0m.")
        return False


#start the program here
def main():
    #store the specified port number, if none was given, alert the user and exit the program
    if(len(sys.argv) > 1):
        serverPort = sys.argv[1]
        if(re.match(Port, serverPort) == None):
            print("ERROR: Port number must be in the range 1024-65353. Additional restrictions to port range may apply to usage.")
            sys.exit()
    else:
        print("ERROR: Port number must be provided\n[./server.py <port number> (contact list)]\nport number necessary, contact list file is optional.\n")
        sys.exit()

    print("Starting IM Server process on port #" + serverPort + "...")
    #if a contact list file was given, load it.
    if(len(sys.argv) > 2):
        print("Loading contacts from list: " + sys.argv[2] + "...")
        load(sys.argv[2])
    print_config()
    save("before")
    exit("gabe")
    save("after")
    register("noob_master69", "192.168.192.255", "60000")
    create("newlist")
    print_config()
    create("otherlist")
    print_config()
    save("edgetest")


if(__name__ == '__main__'):
    main()
