#!/usr/bin/python3

import sys

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
usercount = 0
contact_names = []
listcount = 0
contact_lists = []

def print_config():
    print("Printing configuration...")
    print("Users (count =", usercount + "):")
    for i in range(int(usercount)):
        print("\t" + contact_names[i].name + "," + contact_names[i].ip + "," + contact_names[i].port)
    print("Contact lists (count =", listcount + "):")
    for l in range(int(listcount)):
        print("\tNew List: " + contact_lists[l].name+ "," + contact_lists[l].count)
        for k in range(int(contact_lists[l].count)):
            print("\t\t" + contact_lists[l].members[k].name + "," + contact_lists[l].members[k].ip + "," + contact_lists[l].members[k].port)
    

#save the current config file. return with appropriate response code
def save(filename):
    try:
        return "SUCCESS"
    except:
        return "FAILURE"

#load a passed config file into the contacts. Only meant for startup
def load(filename):
    f = open(filename, "r")
    global usercount, contact_names, listcount, contact_lists
    usercount = f.readline().strip()
    for i in range(int(usercount)):
        person = Person(f.readline().strip().split(","))
        contact_names.append(person)
    listcount = f.readline().strip()
    for l in range(int(listcount)):
        lst = List(f.readline().strip().split(","))
        contact_lists.append(lst)
        for k in range(int(contact_lists[l].count)):
            contact = Person(f.readline().strip().split(","))
            contact_lists[l].members.append(contact)
    f.close()

def main():
    #store the specified port number, if none was given, alert the user and exit the program
    if(len(sys.argv) > 1):
        serverPort = sys.argv[1]
    else:
        print("ERROR: Port number must be provided\n[./server.py <port number> (contact list)]\nport number necessary, contact list file is optional.\n")
        sys.exit()

    print("Starting IM Server process on port #" + serverPort + "...")
    #if a contact list file was given, load it.
    if(len(sys.argv) > 2):
        print("Loading contacts from list: " + sys.argv[2] + "...")
        load(sys.argv[2])
        print("Configuration loaded:")
        print_config()

if(__name__ == '__main__'):
    main()
