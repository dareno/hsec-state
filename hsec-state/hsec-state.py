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


def is_armed(data, pin_id):
    """
    Return true if the pin is in an armed zone
    """
    for zone in data['zones']:
        if data['zones'][zone]["armed"] == "True":
            if pin_id in data['zones'][zone]["members"]:
                return True

    return False
    
def main():
    """ main method """

    # load the wire/sensor model
    with open('config.json') as json_data_file:
        data = json.load(json_data_file)
    #print( json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
    #print( data['zones'])

    # get key for ifttt maker recipe
    config = configparser.ConfigParser()
    config.read('hsec-state.cfg')
    #key=config['maker.ifttt.com']['Key']

    # create object for communication to sensor system
    trigger_comms = comms.SubChannel("tcp://trig1:5563", ['sensor_events','control_events', 'state'])

    # create object for communication to alert system
    alert_comms = comms.PubChannel("tcp://*:5564")

    try:
        while True:

            # Read envelope and address from queue
            rv = trigger_comms.get()

            # if there are events, process them
            if rv is not None:

                [address, contents] = rv
                for item in json.loads(contents.decode('utf8')):
                    if is_armed(data, item[0]):
                        print("alerting on %s" % item[0])
                        alert_comms.send("alarm", data["pins"][item[0]][1])
                    else:
                        pass # maybe just log it

            else:
                # no events waiting for processing
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    # clean up zmq connection
    trigger_comms.close()
    alert_comms.close()

if __name__ == "__main__":
    main()
