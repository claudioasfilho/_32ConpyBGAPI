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

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from common.conversion import Ieee11073Float
from common.util import BluetoothApp, find_service_in_advertisement, PeriodicTimer

# Constants
HEALTH_THERMOMETER_SERVICE = b"\x09\x18"
TEMPERATURE_MEASUREMENT_CHAR = b"\x1c\x2a"

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
SCANNING_PERIOD = 2.0


connectable_device = []
connectable_device_addresses = []

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

def contains(list, filter):
    for x in list:
        if filter(x):
            return True
        return False




class App(BluetoothApp):
    timerCounter = 0
    activeConnection = Connectable_device(0,0,0,0,0,0,0,0)

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

                    activeConnection= Connectable_device(evt.address,evt.address_type, evt.bonding, evt.primary_phy, evt.secondary_phy, evt.adv_sid, evt.tx_power, evt.rssi)

                    # #print(evt)
                    # if activeConnection not in connectable_device_addresses:
                    #     connectable_device_addresses.append(activeConnection)
                    #     print(len(connectable_device_addresses))
                    #print(evt)
                    if evt.address not in connectable_device_addresses:
                        connectable_device_addresses.append(evt.address)
                        print(len(connectable_device_addresses))



        # This event indicates that a new connection was opened.
        elif evt == "bt_evt_connection_opened":
            print("\nConnection opened\n")
            self.conn_properties[evt.connection] = {}
            # Only the last 3 bytes of the address are relevant
            self.conn_properties[evt.connection]["server_address"] = evt.address[9:].upper()
            # Discover Health Thermometer service on the slave device
            # self.lib.bt.gatt.discover_primary_services_by_uuid(
            #     evt.connection,
            #     HEALTH_THERMOMETER_SERVICE)
            # self.conn_state = "discover_services"

        # # This event is generated when a new service is discovered
        # elif evt == "bt_evt_gatt_service":
        #     self.conn_properties[evt.connection]["thermometer_service_handle"] = evt.service
        #
        # # This event is generated when a new characteristic is discovered
        # elif evt == "bt_evt_gatt_characteristic":
        #     self.conn_properties[evt.connection]["thermometer_characteristic_handle"] = evt.characteristic
        #
        # # This event is generated for various procedure completions, e.g. when a
        # # write procedure is completed, or service discovery is completed
        # elif evt == "bt_evt_gatt_procedure_completed":
        #     # If service discovery finished
        #     if self.conn_state == "discover_services":
        #         # Discover thermometer characteristic on the slave device
        #         self.lib.bt.gatt.discover_characteristics_by_uuid(
        #             evt.connection,
        #             self.conn_properties[evt.connection]["thermometer_service_handle"],
        #             TEMPERATURE_MEASUREMENT_CHAR)
        #         self.conn_state = "discover_characteristics"
        #
        #     # If characteristic discovery finished
        #     elif self.conn_state == "discover_characteristics":
        #         # enable indications
        #         self.lib.bt.gatt.set_characteristic_notification(
        #             evt.connection,
        #             self.conn_properties[evt.connection]["thermometer_characteristic_handle"],
        #             self.lib.bt.gatt.CLIENT_CONFIG_FLAG_INDICATION)
        #         self.conn_state = "enable_indication"
        #
        #     # If indication enable process finished
        #     elif self.conn_state == "enable_indication":
        #         # and we can connect to more devices
        #         if len(self.conn_properties) < SL_BT_CONFIG_MAX_CONNECTIONS:
        #             # start scanning again to find new devices
        #             self.lib.bt.scanner.start(
        #                 self.lib.bt.gap.PHY_PHY_1M,
        #                 self.lib.bt.scanner.DISCOVER_MODE_DISCOVER_GENERIC)
        #             self.conn_state = "scanning"
        #         else:
        #             self.conn_state = "running"

        # This event is generated when a connection is dropped
        elif evt == "bt_evt_connection_closed":
            print("Connection closed:", evt.connection)
            del self.conn_properties[evt.connection]
            if self.conn_state != "scanning":
                # start scanning again to find new devices
                self.lib.bt.scanner.start(
                    self.lib.bt.gap.PHY_PHY_1M,
                    self.lib.bt.scanner.DISCOVER_MODE_DISCOVER_GENERIC)
                self.conn_state = "scanning"

        # # This event is generated when a characteristic value was received e.g. an indication
        # elif evt == "bt_evt_gatt_characteristic_value":
        #     self.conn_properties[evt.connection]["temperature"] = Ieee11073Float.from_bytes(evt.value[1:])
        #     # The first byte of the characteristic value is the flags field,
        #     # the first bit in the flags field encodes the temperature unit.
        #     if evt.value[0] & 1:
        #         self.conn_properties[evt.connection]["unit"] = "F"
        #     else:
        #         self.conn_properties[evt.connection]["unit"] = "C"
        #     # Send confirmation for the indication
        #     self.lib.bt.gatt.send_characteristic_confirmation(evt.connection)
        #     # Trigger RSSI measurement on the connection
        #     self.lib.bt.connection.get_rssi(evt.connection)

        # This event is generated when RSSI value was measured
        elif evt == "bt_evt_connection_rssi":
            self.conn_properties[evt.connection]["rssi"] = evt.rssi
            # Print the values
            print("{server_address} [{rssi:4} dBm] {temperature:6.6} {unit}".format(**self.conn_properties[evt.connection]))

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
        else:
            if self.conn_state == "scanning":
                self.timerCounter +=1

        # if self.conn_state == "Connecting_to_devices":
        #     if len(self.conn_properties) < SL_BT_CONFIG_MAX_CONNECTIONS:
        #         self.lib.bt.connection.open(
        #             evt.address,
        #             evt.address_type,
        #             self.lib.bt.gap.PHY_PHY_1M)
        #     else:
        #         self.conn_state = "opening"


# Script entry point.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    # Instantiate the application.
    app = App(parser=parser)
    # Running the application blocks execution until it terminates.
    app.run()
