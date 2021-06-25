# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2014 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
"""
Simple example that connects to the first Crazyflie found, logs the Stabilizer
and prints it to the console. While logging, the file executes helper functions called
from Clojure side as whenever.
This file is referenced and adapted from basiclog.py and ramp.py
"""
import logging
import time
import numpy as np
from threading import Timer
from threading import Thread

import cflib.crtp  # noqa
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.utils import uri_helper

uri = uri_helper.uri_from_env(default="radio://0/80/250K/E7E7E7E7E7")

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


class Interface:
    """
    Simple logging example class that logs the Stabilizer from a supplied
    link uri and disconnects after 5s.
    """

    sequence = [
        # x, y, z (in m), yaw
        (2.5, 2.5, 1.2, 0),
        (1.5, 2.5, 1.2, 0),
        (2.5, 2.0, 1.2, 0),
        (3.5, 2.5, 1.2, 0),
        (2.5, 3.0, 1.2, 0),
        (2.5, 2.5, 1.2, 0),
        (2.5, 2.5, 0.4, 0),
    ]

    def __init__(self, link_uri):
        """Initialize and run the example with the specified link_uri"""
        # Initialize the low-level drivers
        cflib.crtp.init_drivers()

        self._cf = Crazyflie(rw_cache="./cache")

        # Connect some callbacks from the Crazyflie API
        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        print("Connecting to %s" % link_uri)

        # Try to connect to the Crazyflie
        self._cf.open_link(link_uri)

        # Variable for storing all the variables in a list
        self.global_list = []

        # Variable used to keep main loop occupied until disconnect
        self.is_connected = True

        # Variables used to execute helper functions
        self.should_fly = False
        self.should_display = False
        self.input_thrust = 0
        self.default_pitch = 0
        self.default_roll = 0
        self.default_yaw = 0

    def _connected(self, link_uri):
        """This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        print("Connected to %s" % link_uri)

        # The definition of the logconfig can be made before connecting
        self._lg_stab = LogConfig(name="StateEstimate", period_in_ms=100)
        self._lg_stab.add_variable("stateEstimate.roll", "float")
        self._lg_stab.add_variable("stateEstimate.pitch", "float")
        self._lg_stab.add_variable("stateEstimate.yaw", "float")
        self._lg_stab.add_variable("stateEstimate.z", "float")
        self._lg_stab.add_variable("baro.asl", "float")

        # Adding the configuration cannot be done until a Crazyflie is
        # connected, since we need to check that the variables we
        # would like to log are in the TOC.
        try:
            self._cf.log.add_config(self._lg_stab)
            # This callback will receive the data
            self._lg_stab.data_received_cb.add_callback(self._stab_log_data)
            # This callback will be called on errors
            self._lg_stab.error_cb.add_callback(self._stab_log_error)
            # Start the logging
            self._lg_stab.start()
        except KeyError as e:
            print(
                "Could not start log configuration,"
                "{} not found in TOC".format(str(e))
            )
        except AttributeError:
            print("Could not add Stabilizer log config, bad configuration.")

        # Start a timer to disconnect in 5s
        # t = Timer(5, self._cf.close_link)
        # t.start()

    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print("Error when logging %s: %s" % (logconf.name, msg))

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback from a the log API when data arrives"""
        temp_list = []
        # print(f"[{timestamp}][{logconf.name}]: ", end="")
        for name, value in data.items():
            # print(f"{name}: {value:3.3f} ", end="")
            temp_list.append(value)
        # print()
        self.global_list = list(
            np.around(np.array(temp_list), 2)
        )  # store the global list as 2dp format

        # conduct a series of check for drone to perform certain functions called by clojure
        if self.should_display:
            Thread(target=self.return_list_helper()).start()
        if self.should_fly:
            Thread(target=self.take_off_helper()).start()

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the specified address)"""
        print("Connection to %s failed: %s" % (link_uri, msg))
        self.is_connected = False

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print("Connection to %s lost: %s" % (link_uri, msg))

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print("Disconnected from %s" % link_uri)
        self.is_connected = False

    def manually_disconnect(self):
        """Helper function to allow manual disconnection on clojure side after 1 second of delay"""
        t = Timer(1, self._cf.close_link)
        t.start()

    def return_list_helper(self):
        """Helper function to return real time data on clojure side"""
        print("The list has been returned:.{}".format(self.global_list))
        # time.sleep(0.1)
        self.should_display = False
        return self.global_list

    def return_list(self):
        self.should_display = True
        return self.global_list

    def take_off_helper2(self):
        self._cf.commander.send_velocity_world_setpoint(
            0, 0, 0.1, 0
        )  # vx, vy, vz, yawrate
        time.sleep(2)
        self.should_fly = False

    def take_off_helper(self):
        # orientation is with reference to the blue lights closer towards user
        print("Time to take off!")
        thrust_mult = 1
        thrust_step = 500  # increment unit
        thrust = self.input_thrust  # upwards vertical force
        thrust_limit = thrust + 5000  # set limit to the max thrust
        # set roll, pitch, yaw as default values first
        pitch = self.default_pitch  # tilt upwards for positive (e.g. like lifting off)
        roll = self.default_roll  # tilt sideways (right for positive)
        yawrate = self.default_yaw  # rotate anti-clockwise for positive values
        countdown = 3

        # Unlock startup thrust protection
        self._cf.commander.send_setpoint(0, 0, 0, 0)

        # while thrust >= self.input_thrust:
        while countdown > 0:
            print("current thrust:", thrust)
            self._cf.commander.send_setpoint(roll, pitch, yawrate, thrust)
            time.sleep(0.1)
            if thrust >= thrust_limit:
                thrust_mult = -1  # start the descent
            thrust += thrust_step * thrust_mult
            countdown -= 0.2
        self._cf.commander.send_setpoint(0, 0, 0, 0)
        # Make sure that the last packet leaves before the link is closed
        # since the message queue is not flushed before closing
        time.sleep(0.1)
        self.should_fly = False  # retrieve back permission
        # reset all the values for thrust, roll, pitch and yaw
        self.input_thrust = 0  # reset the thrust as a defensive precaution
        self.default_roll = 0
        self.default_pitch = 0
        self.default_yaw = 0

    def take_off(self, action, thrust=25000):
        self.should_fly = True
        self.input_thrust = thrust
        if action == "right":
            self.default_roll = 2
        elif action == "left":
            self.default_roll = -2
        elif action == "forward":
            self.default_pitch = 2
        elif action == "backward":
            self.default_pitch = -2
        elif action == "upwards":
            pass

    def run_sequence(self):
        for position in self.sequence:
            print("Setting position {}".format(position))
            for i in range(50):
                self._cf.commander.send_position_setpoint(
                    position[0], position[1], position[2], position[3]
                )
                time.sleep(0.1)

        self._cf.commander.send_stop_setpoint()
        # Make sure that the last packet leaves before the link is closed
        # since the message queue is not flushed before closing
        time.sleep(0.1)
        self.should_fly = False


if __name__ == "__main__":
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    le = Interface(uri)

    # The Crazyflie lib doesn't contain anything to keep the application alive,
    # so this is where your application should do something. In our case we
    # are just waiting until we are disconnected.
    while le.is_connected:
        time.sleep(1)
