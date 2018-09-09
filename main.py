#!/usr/bin/python3

import serial
import json
import time
import sys

# load configuration

def load_config():
    with open("config.json","r") as c, open("keys.json","r") as k:
        config = json.load(c)
        keys = json.load(k)
        good_members = []
        members = []
        for x in keys:
            if keys[x]["door"] == 1:
                good_members.append(keys[x["id"]])
            members.append(keys[x["id"]])
    return (config,keys,good_members,members)

# initialise relay

def relay_init():
    return serial.Serial(config["serial"]["pointer"], baudrate=config["serial"]["baudrate"])

def unlock_door(relays, t=5):
    relays.write('A')
    time.sleep(t)
    relays.write('a')

def check(id):
    if id in good_members:
        return True
    else:
        return False

def speaker(sound):
    os.system ("mpg123 -q {} &".format(config["sounds"][sound]))

def notify(message,door_activity=False):
    print(message)

# load config

config,keys,good_members,members = load_config()

# initiate serial connection

s = relay_init()

# turn on relay

time.sleep(5)
s.write('B')

notify("{} has started".format(config["name"]))

# begin listening for RFID

while True:
    try:
        while s.inWaiting() > 0:
            data = s.readline()
            if "RFID" in data:
                card = data[-11:-1]
                if card in good_members:
                    notify("{} ({}) unlocked the door.".format(keys[card]["name"],card), True)
                    speaker("granted")
                    if len(keys[card]["groups"]) > 0:
                        for x in keys[card]["groups"]
                            notify("x")
                    if "delayed" = keys[card]["groups"]:
                        unlock_door(s,30)
                    else:
                        unlock_door()
                elif card in members:
                    notify("{} ({}) attempted to unlock the door but was denied because they are not part of the door group.".format(keys[card]["name"],card), True)
                    speaker("denied")
                else:
                    notify("Someone attempted to use an unknown key to open the door. Tag ID: {}".format(card), True)
                    speaker("denied")
    except (SystemExit, KeyboardInterrupt):
        notify("{} is shutting down.".format(config["name"]))
