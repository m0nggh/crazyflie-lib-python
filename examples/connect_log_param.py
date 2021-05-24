import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

uri = 'radio://0/80/250K/E7E7E7E7E7'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


def simple_connect():
    print("Yeah, I'm connected! :D")
    time.sleep(3)
    print("Now I will disconnect :'(")

# this is for synchronous access of log data from the drone firmeware itself which means that it reads out the logging in the function directly in the loop


def simple_log(scf, logconf):

    with SyncLogger(scf, lg_stab) as logger:

        for log_entry in logger:

            timestamp = log_entry[0]
            data = log_entry[1]
            logconf_name = log_entry[2]

            list = []
            for name, value in data.items():
                text = "{}: {}"
                print(text.format(name, value))
                list.append(value)
            print(list)

# this helper function allows you to manipulate the log data as you wish to


def log_stab_callback(timestamp, data, logconf):
    list = []
    for name, value in data.items():
        text = "{}: {}"
        print(text.format(name, value))
        list.append(value)
    print("The current values are: {}".format(list))
    return list

# Logging variables can be received separately from this function, in a callback independently of the main loop-rate


def simple_log_async(scf, logconf):
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()  # logconf needs to be started manually and stopped
    time.sleep(10)  # can set to a very huge number so the logconf takes in values continuously
    logconf.stop()


if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    lg_stab = LogConfig(name='StateEstimate', period_in_ms=40)  # min 10ms, currently set to 1s, default is 40ms
    # only can contain up to 26bytes
    lg_stab.add_variable('stateEstimate.roll', 'float')
    lg_stab.add_variable('stateEstimate.pitch', 'float')
    lg_stab.add_variable('stateEstimate.yaw', 'float')
    # lg_stab.add_variable('stateEstimate.x', 'float')
    # lg_stab.add_variable('stateEstimate.y', 'float')
    # lg_stab.add_variable('stateEstimate.z', 'float')
    # lg_stab.add_variable('stabilizer.thrust', 'float')
    # lg_stab.add_variable('acc.x', 'float')

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:

        simple_log_async(scf, lg_stab)
