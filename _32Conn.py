#!/usr/bin/env python3
"""
32 Connections example
"""

# Copyright 2021 Silicon Laboratories Inc. www.silabs.com
#
# SPDX-License-Identifier: Zlib
#
# The licensor of this software is Silicon Laboratories Inc.
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

import argparse
import os.path
import sys
import datetime
from datetime import date, datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from common.conversion import Ieee11073Float
from common.util import BluetoothApp, find_service_in_advertisement, PeriodicTimer

# Constants
HEALTH_THERMOMETER_SERVICE = b"\xe0\x0c\xae\x94\xe6\x22\x6a\xbd\x93\x42\x68\xe3\xd8\xfc\xd9\x42"#b"\x09\x18"
TEMPERATURE_MEASUREMENT_CHAR = b"\x8e\x66\x58\x63\x74\xdf\x5b\x81\x05\x40\x9c\x2f\xf6\x55\x48\x3a"#b"\x1c\xa"

CONN_INTERVAL_MIN = 80   # 100 ms
CONN_INTERVAL_MAX = 80   # 100 ms
CONN_SLAVE_LATENCY = 0   # no latency
CONN_TIMEOUT = 100       # 1000 ms
CONN_MIN_CE_LENGTH = 0
CONN_MAX_CE_LENGTH = 65535

SCAN_INTERVAL = 16       # 10 ms
SCAN_WINDOW = 16         # 10 ms
SCAN_PASSIVE = 0

# The maximum number of connections has to match with the configuration on the target side.
SL_BT_CONFIG_MAX_CONNECTIONS = 32


TIMER_PERIOD = 1.0
SCANNING_PERIOD = 5.0


connectable_device = []
connectable_device_objects = []
connectable_device_addresses = []
init_time = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
final_time = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

class Connectable_device:
    def __init__(self, address, address_type, bonding, primary_phy, secondary_phy, adv_sid, tx_power, rssi):
        self.address = address
        self.address_type = address_type
        self.bonding = bonding
        self.primary_phy = primary_phy
        self.secondary_phy = secondary_phy
        self.adv_sid = adv_sid
        self.tx_power = tx_power
        self.rssi = rssi


class App(BluetoothApp):
    timerCounter = 0
    activeConnection = Connectable_device(0,0,0,0,0,0,0,0)
    connectionHandleCnt = 0
    connectionsMadeCnt = 0
    connAvailable = 0
    Notification_Handler = 0
    initial_time = 0
    final_time = 0

    def contains(list, address):
        for x in list:
            if x.address == address:
                return True
            return False

    def createFile(self, connection, handler, address):
        original_stdout = sys.stdout # Save a reference to the original standard output
        with open('dataFromConn'+ str(connection) + '.txt', 'w') as f:
            sys.stdout = f # Change the standard output to the file we created
            print("Connection address: " + str(address) + "\n")
            print("Connection #: " + str(connection) + "\n")
            print("Connection handler#: " + str(handler) + "\n")
            # self.initial_time = datetime.now()
            # print(str(self.initial_time) + "\n")

        sys.stdout = original_stdout # Reset the standard output to its original value

    def appendFile(self, connection, handler, data):
        original_stdout = sys.stdout # Save a reference to the original standard output
        with open('dataFromConn'+ str(connection) + '.txt', 'a') as f:
            sys.stdout = f # Change the standard output to the file we created
            print(data)
            # self.final_time = datetime.now()
            # print(str(datetime.now()) + "\n")
        sys.stdout = original_stdout # Reset the standard output to its original value

    """ Application derived from generic BluetoothApp. """
    def event_handler(self, evt):
        """ Override default event handler of the parent class. """
        # This event indicates the device has started and the radio is ready.
        # Do not call any stack command before receiving this boot event!
        if evt == "bt_evt_system_boot":
            # Set passive scanning on 1Mb PHY
            self.lib.bt.scanner.set_mode(self.lib.bt.gap.PHY_PHY_1M, SCAN_PASSIVE)
            # Set scan interval and scan window
            self.lib.bt.scanner.set_timing(self.lib.bt.gap.PHY_PHY_1M, SCAN_INTERVAL, SCAN_WINDOW)
            # Set the default connection parameters for subsequent connections
            self.lib.bt.connection.set_default_parameters(
                CONN_INTERVAL_MIN,
                CONN_INTERVAL_MAX,
                CONN_SLAVE_LATENCY,
                CONN_TIMEOUT,
                CONN_MIN_CE_LENGTH,
                CONN_MAX_CE_LENGTH)
            # Start scanning - looking for thermometer devices
            self.lib.bt.scanner.start(
                self.lib.bt.gap.PHY_PHY_1M,
                self.lib.bt.scanner.DISCOVER_MODE_DISCOVER_GENERIC)
            self.conn_state = "scanning"
            self.timer = PeriodicTimer(period=TIMER_PERIOD, target=self.timer_handler)
            self.timer.start()
            self.conn_properties = {}

        # This event is generated when an advertisement packet or a scan response
        # is received from a responder
        elif evt == "bt_evt_scanner_scan_report":
            # Parse advertisement packets
            if evt.packet_type == 0:
                # If a thermometer advertisement is found...
                if find_service_in_advertisement(evt.data, HEALTH_THERMOMETER_SERVICE):

                    self.activeConnection= Connectable_device(evt.address,evt.address_type, evt.bonding, evt.primary_phy, evt.secondary_phy, evt.adv_sid, evt.tx_power, evt.rssi)

                    if evt.address not in connectable_device_addresses:
                        connectable_device_addresses.append(evt.address)
                        # print(len(connectable_device_addresses))


        # This event indicates that a new connection was opened.
        elif evt == "bt_evt_connection_opened":
            print("\nConnection opened Address:" + str(evt.address))

            self.createFile(evt.connection, self.connectionHandleCnt, evt.address)

            self.connectionHandleCnt +=1
            self.connectionsMadeCnt +=1
            self.conn_properties[evt.connection] = {}
            # Only the last 3 bytes of the address are relevant
            self.conn_properties[evt.connection]["server_address"] = evt.address[9:].upper()

            if self.connectionsMadeCnt == self.connAvailable:
                self.conn_state = "Done_connecting"
                self.Notification_Handler = 1
            else:
                self.conn_state = "Connections_In_Progress"

        # This event is generated when a connection is dropped
        elif evt == "bt_evt_connection_closed":
            print("Connection closed:", evt.connection)
            #print("\nConnection closed Address:" + str(evt.address))
            del self.conn_properties[evt.connection]
            self.connectionHandleCnt -=1
            self.connectionsMadeCnt -=1

        # This event is generated when RSSI value was measured
        elif evt == "bt_evt_connection_rssi":
            self.conn_properties[evt.connection]["rssi"] = evt.rssi
            # Print the values
            print("{server_address} [{rssi:4} dBm] {temperature:6.6} {unit}".format(**self.conn_properties[evt.connection]))

        elif evt == "bt_evt_gatt_procedure_completed":
            # If service discovery finished
            if self.conn_state == "receiving_notifications":
                # Discover thermometer characteristic on the slave device
                print("Notifications enabled on connection# " + str(evt.connection))

        elif evt == "bt_evt_gatt_characteristic_value":
            if self.conn_state == "receiving_notifications":
                #self.Notification_Handler = evt.connection
                self.final_time = datetime.now()
                # final_time.append(self.final_time)
                print("evt.connection" + str(evt.connection))
                final_time[evt.connection - 1] = self.final_time
                self.appendFile(evt.connection, self.connectionHandleCnt, evt.value)

    def timer_handler(self):
        # print(self.timerCounter)
        """ Timer Handler """
        if self.timerCounter >= SCANNING_PERIOD and self.conn_state == "scanning":
            self.timerCounter = 0
            # Stops Scanning
            self.lib.bt.scanner.stop()
            print("Scanning Stopped, connecting to devices")
            self.conn_state = "Connecting_to_devices"
            print(connectable_device_addresses)
            print(connectable_device_objects)

        else:
            if self.conn_state == "scanning":
                self.timerCounter +=1

        if self.conn_state == "Connecting_to_devices":
            #It checks how many devices are availabe for Connection
            self.connAvailable = len(connectable_device_addresses)
            #In case the number of devices available is higher than SL_BT_CONFIG_MAX_CONNECTIONS
            #It will force to be SL_BT_CONFIG_MAX_CONNECTIONS
            if self.connAvailable > SL_BT_CONFIG_MAX_CONNECTIONS:
                self.connAvailable = SL_BT_CONFIG_MAX_CONNECTIONS

            print("Number of connectable devices " + str(self.connAvailable))
            #It initializes the counter for the connections
            self.connectionHandleCnt = 0
            self.conn_state = "Connections_In_Progress"

        if self.conn_state == "Connections_In_Progress":

            if self.connectionsMadeCnt < self.connAvailable:

                self.lib.bt.connection.open(connectable_device_addresses[self.connectionHandleCnt],0,self.lib.bt.gap.PHY_PHY_1M)
                self.conn_state = "opening_connection"
            # else:
            #     self.conn_state = "opening"
        if self.conn_state == "Done_connecting":
            self.timerCounter = 0
            self.conn_state = "receiving_notifications"
            print("self.conn_state == Done_connecting " + str(self.Notification_Handler))



        if self.conn_state == "receiving_notifications":
            if self.Notification_Handler <= self.connAvailable:
                self.initial_time = datetime.now()
                #init_time.append(self.initial_time)
                init_time[self.Notification_Handler - 1] = self.initial_time
                self.appendFile(self.Notification_Handler, self.Notification_Handler, self.initial_time)
                self.lib.bt.gatt.set_characteristic_notification(self.Notification_Handler, 21, 1)
                self.Notification_Handler += 1

            if self.timerCounter == 5:
                print(final_time)
                print(init_time)
                print("self.connAvailable " + str(self.connAvailable))
                i = 0
                while i < self.connAvailable:
                    connectionStamp = "Connection #" + str(i+1) + "\n" + "Final Time:" + str(final_time[i])
                    self.appendFile(i+1, i+1, connectionStamp)
                    #self.appendFile(i+1, i+1, final_time[i])
                    delta = final_time[i] - init_time[i]
                    connectionStamp = "Final Time - Initial time = " + str(delta)
                    self.appendFile(i+1, i+1, connectionStamp)
                    #self.appendFile(i+1,i+1, delta )
                    i += 1




            self.timerCounter +=1

        print(self.conn_state)

# Script entry point.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    # Instantiate the application.
    app = App(parser=parser)
    # Running the application blocks execution until it terminates.
    app.run()
