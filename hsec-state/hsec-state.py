#!/usr/bin/env python3.4
"""
Receive events, decide what to do. Based on zguide.
"""
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import requests             # for webhooks
import configparser         # for reading config
import time
import comms.comms as comms # for getting a channel to the sensor
import json                 # transferring data over comms, format of data model


def arm(data, zoneToUpdate):
    print("arming %s" % zoneToUpdate )
    for zone in data['zones']:
        if zone==zoneToUpdate:
            data['zones'][zone]["armed"] = "True"

def disarm(data, zoneToUpdate):
    NotFound = True
    for zone in data['zones']:
        if zone==zoneToUpdate:
            print("disarming %s" % zoneToUpdate )
            data['zones'][zone]["armed"] = "False"
            NotFound=False
    if (NotFound):
        print("unrecognized zone: %s" % zoneToUpdate )

def zone_is_armed(zone):
    print("checking to see if %s is armed..." % zone)
    return False

def is_armed(data, pin_id):
    """
    Return true if the pin is in an armed zone
    """
    for zone in data['zones']:
        if data['zones'][zone]["armed"] == "True":
            if pin_id in data['zones'][zone]["members"]:
                return True

    return False

def print_arm_status():
    pass

def main():
    """ main method """

    # load the wire/sensor model
    with open('config.json') as json_data_file:
        data = json.load(json_data_file)

    #print( json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
    #print( data['zones'])


    # create object for communication to control system
    #control_comms = comms.SubChannel("tcp://webui1:5563", ['control_events'])
    control_comms = comms.SubChannel("tcp://node1:5563", ['control_events'])

    # create object for communication to sensor system
    trigger_comms = comms.SubChannel("tcp://trigger1:5563", ['sensor_events','control_events', 'state'])

    # create object for communication to interested parties (e.g. alert)
    send_comms = comms.PubChannel("tcp://*:5564")

    try:
        while True:

            # Read envelope and address from queue
            control_commands = control_comms.get()

            # if there are events, process them
            if control_commands is not None:

                [address, contents] = control_commands
                for item in json.loads(contents.decode('utf8')):
                    print("contents=%s, Received control command %s, item[0]=%s, item[1]=%s" 
                            % (contents, item, item[0], item[1])
                    )
                    if item[1]=="arm":
                        arm(data,item[0])
                    elif item[1]=="disarm":
                        disarm(data,item[0])
                    elif item[1]=="status":
                        # send status
                        send_comms.send("state", data)
                    else:
                        print("Error! Received unknown command %s" % item[1])

            send_comms.send("state", data) # just send some state sometimes...

            # Read envelope and address from queue
            rv = trigger_comms.get()

            # if there are events, process them
            if rv is not None:

                [address, contents] = rv
                for item in json.loads(contents.decode('utf8')):
                    if is_armed(data, item[0]):
                        #print("alerting on %s" % item[0])
                        print("alerting on %s" % data["pins"][item[0]][1])
                        send_comms.send("alarm", data["pins"][item[0]][1])
                    else:
                        #print("Not alerting on %s" % item[0])
                        print("Not alerting on %s" % data["pins"][item[0]][1])
                        pass # maybe just log it

            else:
                # no events waiting for processing
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    # clean up zmq connection
    trigger_comms.close()
    send_comms.close()

if __name__ == "__main__":
    main()
