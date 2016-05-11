#!/usr/bin/env python3.4
"""
Receive events, decide what to do. Based on zguide.
"""
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import requests             # for webhooks
import configparser         # for reading config
import time
import comms.comms as comms # for getting a channel to the sensor


def main():
    """ main method """

    # get key for ifttt maker recipe
    config = configparser.ConfigParser()
    config.read('hsec-state.cfg')
    key=config['maker.ifttt.com']['Key']

    # create object for communication to sensor system
    trigger_comms = comms.SubChannel("tcp://localhost:5563", ['sensor_events','control_events', 'state'])

    # create object for communication to alert system
    alert_comms = comms.PubChannel("tcp://*:5564")


    try:
        while True:
            # #####################################
            # check to see if state should change
            # possible states:
            #  - unarmed
            #  - arm for doors
            #  - arm for doors and 1st floor windows
            #  - arm for doors and all windows
            #  - arm for doors, windows and interior motion


            # #####################################
            # process events
            # Read envelope and address from queue
            rv = trigger_comms.get()
            if rv is not None:
                # there has been an event
                [address, contents] = rv
                print("state event: [%s] %s" % (address, contents))

                # should I alert on the event? Check state and alert if armed
                alert_comms.send("state",["Initial state"])

            else:
                # no events waiting for processing
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    # clean up zmq connection
    subscriber.close()
    context.term()

if __name__ == "__main__":
    main()
