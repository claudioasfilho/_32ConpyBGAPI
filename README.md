#32ConnectionsCableReplacementtest

This host code works in conjunction with a custom BLE NCP code, that supports up to 32 Connections and custom End Device. It uses the PYBGAPI library for Python3.

It scans for a fixed period of time, defined by SCANNING_PERIOD and searches for devices advertising a custom service (UUID 42d9fcd8-e368-4293-bd6a-22e694ae0ce0).

It will identify the number of connectable devices and then Connect to each one of them, set the connection parameters and also set the PHY to 2M in every single connection.

Then it will subscribe to the data notifications which will push a text file with approximately 5KB. At the end of the test, it will generate a text file for each connection created with the Custom End devices and will hold the data received over the air and also with the time that it took to receive the full payload of data.

SDK Tested: Silicon Labs Bluetooth SDK 3.3.2
Python 3.9.12


Notes:

This was tested up to 16 simultaneous connections
