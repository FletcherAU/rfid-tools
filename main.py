#!/usr/bin/python3

import serial
import json
import time
import sys
import os
from slackclient import SlackClient

# load configuration

def load_config():
    with open("config.json","r") as c, open("keys.json","r") as k:
        config = json.load(c)
        keys = json.load(k)
        active_members = []
        members = []
        for x in keys:
            if keys[x]["door"] == 1:
                active_members.append(x)
            members.append(x)
    return (config,keys,active_members,members)


def relay_init():
    """Initialise relays using serial settings from config"""
    return serial.Serial(config["serial"]["pointer"], baudrate=config["serial"]["baudrate"])

def unlock_door(relays, t=5):
    """Unlock door for t seconds"""
    relays.write('A'.encode())
    time.sleep(t)
    relays.write('a'.encode())

def check(id):
    """Check whether member ID is active"""
    if id in active_members:
        return True
    else:
        return False

def speaker(sound):
    """Play requested sound, if found in config."""
    if config["sounds"].get(sound, ''):
        os.system ("mpg123 -q {} &".format(config["sounds"][sound]))
    else:
        notify(door_activity=False,status="Nonexistent sound '{}' requested".format(sound))

    os.system ("mpg123 -q {} &".format(config["sounds"][sound]))

def notify(door_activity=False,id=" ",name=" ",status=" "):
    if door_activity:
        attachments = [{"fallback":"An image of the front door",
                          "image_url":"http://space.artifactory.org.au/foyer.jpg"},
                       {"fallback":"An image of the carpark",
                          "image_url":"http://space.artifactory.org.au/carpark.jpg"}]
        fields = [{"title":"Name",
                   "value":name,
                   "short":True},
                  {"title":"RFID",
                   "value":id,
                   "short":True},
                  {"title":"Status",
                   "value":status,
                   "short":True}]
        slack.api_call("chat.postMessage",channel=config["slack"]["channel"],text="Someone interacted with the door",attachments=attachments,fields=fields,)
    else:
        print(status)

# load config

config,keys,good_members,members = load_config()

# initiate slack client

slack = SlackClient(config["slack"]["token"])

# initiate serial connection

s = relay_init()

# turn on relay

time.sleep(5)
s.write('B'.encode())

notify(door_activity=False,status="{} has started".format(config["name"]))

# begin listening for RFID

while True:
    try:
        while s.inWaiting() > 0:
            data = s.readline().decode()
            if "RFID" in data:
                card = data[-11:-1]
                if card in good_members:
                    notify(door_activity=False,status="{} ({}) unlocked the door.".format(keys[card]["name"],card))
                    speaker("granted")
                    if len(keys[card]["groups"]) > 0:
                        for x in keys[card]["groups"]:
                            notify(door_activity=False,status=x)
                    if "delayed" == keys[card]["groups"]:
                        unlock_door(s,30)
                    else:
                        unlock_door(s)
                elif card in members:
                    keys[card]["name"],card
                    notify(door_activity=True,id=card,name=keys[card]["name"],status="Known but blocked")
                    notify(door_activity=False,status="{} ({}) attempted to unlock the door but was denied because they are not part of the door group.".format(keys[card]["name"],card))
                    speaker("denied")
                else:
                    notify(door_activity=True,id=card,name="Unknown",status="An unknown card was used, new cards can be added via TidyHQ")
                    notify(door_activity=False,status="Someone attempted to use an unknown key to open the door. Tag ID: {}".format(card))
                    speaker("denied")
    except (SystemExit, KeyboardInterrupt):
        notify(door_activity=False,status="{} is shutting down.".format(config["name"]))
        break
