import logging
import time
import numpy as np
from threading import Timer

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

uri = "radio://0/80/250K/E7E7E7E7E7"
globalList = []

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


class Interface:
    """
    Interface class that logs and extracts live data from the crazyflie at regular intervals of 1s
    """

    uri = "radio://0/80/250K/E7E7E7E7E7"

    def __init__(self):
        """Initialize and run the example with the specified link_uri"""
        # Initialize the low-level drivers
        cflib.crtp.init_drivers()
        print(uri)
        self._cf = Crazyflie(rw_cache="./cache")

        lg_stab = LogConfig(
            name="StateEstimate", period_in_ms=100
        )  # min 10ms, currently set to 1s, default is 40ms
        # only can contain up to 26bytes
        lg_stab.add_variable("stateEstimate.roll", "float")
        lg_stab.add_variable("stateEstimate.pitch", "float")
        lg_stab.add_variable("stateEstimate.yaw", "float")
        # lg_stab.add_variable('stateEstimate.x', 'float')
        # lg_stab.add_variable('stateEstimate.y', 'float')
        # lg_stab.add_variable('stateEstimate.z', 'float')
        # lg_stab.add_variable('stabilizer.thrust', 'float')
        # lg_stab.add_variable('acc.x', 'float')

        with SyncCrazyflie(uri, self._cf) as scf:

            # self.simple_connect()
            self.simple_log_async(scf, lg_stab)
            print("is the function even working")

    # added intermediate functions to test if the list can be returned properly

    def displayList(self, tempList):
        print("The current values are: {}".format(tempList))

    # Logging variables can be received separately from this function, in a callback independently of the main loop-rate

    def simple_log_async(self, scf, logconf):
        self._cf = scf.cf
        self._cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(self.log_stab_callback)
        logconf.start()  # logconf needs to be started manually and stopped
        time.sleep(
            10
        )  # can set to a very huge number so the logconf takes in values continuously
        logconf.stop()

    def log_stab_callback(self, timestamp, data, logconf):
        tempList = []
        global globalList
        for name, value in data.items():
            text = "{}: {:.2f}"
            print(text.format(name, value))
            tempList.append(value)
        # updating the global list consistently
        # globalList = list(tempList)
        globalList = list(
            np.around(np.array(tempList), 2)
        )  # if 2 decimal places is needed

    def simple_connect(self):
        print("Yeah, I'm connected! :D")
        time.sleep(3)
        print("Now I will disconnect :'(")

    def returnList(self):
        print("hello world")
        return globalList


# def simple_connect():
#     print("Yeah, I'm connected! :D")
#     time.sleep(3)
#     print("Now I will disconnect :'(")


# # this is for synchronous access of log data from the drone firmeware itself which means that it reads out the logging in the function directly in the loop


# def simple_log(scf, logconf):

#     with SyncLogger(scf, lg_stab) as logger:

#         for log_entry in logger:

#             timestamp = log_entry[0]
#             data = log_entry[1]
#             logconf_name = log_entry[2]

#             tempList = []
#             for name, value in data.items():
#                 text = "{}: {}"
#                 print(text.format(name, value))
#                 tempList.append(value)
#             # instead of returning the list, have to intercept at this point and take the values consistently
#             displayList(tempList)


# # this helper function allows you to manipulate the log data as you wish to


# def log_stab_callback(timestamp, data, logconf):
#     tempList = []
#     global globalList
#     for name, value in data.items():
#         text = "{}: {:.2f}"
#         print(text.format(name, value))
#         tempList.append(value)
#     # updating the global list consistently
#     # globalList = list(tempList)
#     globalList = list(np.around(np.array(tempList), 2))  # if 2 decimal places is needed


# # added intermediate functions to test if the list can be returned properly


# def displayList(tempList):
#     print("The current values are: {}".format(tempList))


# # Logging variables can be received separately from this function, in a callback independently of the main loop-rate


# def simple_log_async(scf, logconf):
#     cf = scf.cf
#     cf.log.add_config(logconf)
#     logconf.data_received_cb.add_callback(log_stab_callback)
#     logconf.start()  # logconf needs to be started manually and stopped
#     time.sleep(
#         10
#     )  # can set to a very huge number so the logconf takes in values continuously
#     logconf.stop()


# if __name__ == "__main__":
#     # Initialize the low-level drivers
#     cflib.crtp.init_drivers()
#     print("drivers have started!")

#     lg_stab = LogConfig(
#         name="StateEstimate", period_in_ms=1000
#     )  # min 10ms, currently set to 1s, default is 40ms
#     # only can contain up to 26bytes
#     lg_stab.add_variable("stateEstimate.roll", "float")
#     lg_stab.add_variable("stateEstimate.pitch", "float")
#     lg_stab.add_variable("stateEstimate.yaw", "float")
#     # lg_stab.add_variable('stateEstimate.x', 'float')
#     # lg_stab.add_variable('stateEstimate.y', 'float')
#     # lg_stab.add_variable('stateEstimate.z', 'float')
#     # lg_stab.add_variable('stabilizer.thrust', 'float')
#     # lg_stab.add_variable('acc.x', 'float')

#     with SyncCrazyflie(uri, cf=Crazyflie(rw_cache="./cache")) as scf:

#         simple_log_async(scf, lg_stab)

# displayList(returnList())  # to test if the calling of function works
