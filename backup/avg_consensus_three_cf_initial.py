#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#  Copyright © 2019 The Regents of the University of Michigan


import math
import logging
import time
from threading import Timer


import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger


# Change uris according to your setup
URI0 = 'radio://0/80/2M/E7E7E7E7E7'
URI1 = 'radio://0/80/2M/E7E7E7E7E8'
#URI2 = 'radio://0/80/2M/E7E7E7E7E9'
# d: diameter of circle
# z: altituce
params0 = {'base': 0.15, 'h': 1.0, 'num': 0}
params1 = {'base': 0.15, 'h': 0.4, 'num': 1}
#params2 = {'base': 0.40, 'h': 1.6}

uris = {
    URI0,
    URI1,
#    URI2,
}

params = {
    URI0: [params0],
    URI1: [params1],
#    URI2: [params2],
}

currentPos = [0,0]
nextPos = [0,0]

def reset_estimator(scf):
    cf = scf.cf

    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)

# def height_log(scf):
#     log_config = LogConfig(name='Height', period_in_ms=1000)
#     log_config.add_variable('stateEstimate.z', 'float')

#     with SyncLogger(scf, log_config) as logger:
#         for log_entry in logger:
#             data = log_entry[1]
#             print(data)


def poshold(cf, t, z):

    steps = t * 10

    for r in range(steps):
        cf.commander.send_hover_setpoint(0, 0, 0, z)
        time.sleep(0.1)

def consensus(currentPosition):
    #print(currentPosition)
    if len(currentPosition) == 2: 
        nextPos[0] = 0.5 *(currentPosition[0] + currentPosition[1])
        nextPos[1] = 0.5 *(currentPosition[0] + currentPosition[1])
        #print(nextPos)

    elif len(currentPosition) == 3:
        if droneNumber == 0:
            nextPos[0] = 0.5   *(currentPosition[0] + currentPosition[1])
            nextPos[1] = 0.333 *(currentPosition[0] + currentPosition[1] + currentPosition[2])
            nextPos[2] = 0.5   *(currentPosition[1] + currentPosition[2])


def run_sequence(scf, params):
    cf = scf.cf
    base = params['base']
    z = params['h']


    # Base altitude in meters
    end = 0.3
    base = params['base']
    h = params['h']
    num = params['num']

    poshold(cf, 2, base)
    poshold(cf, 5, h)

     # The definition of the logconfig can be made before connecting
    log_config = LogConfig(name='Height', period_in_ms=50)
    log_config.add_variable('stateEstimate.z', 'float')
    with SyncLogger(scf, log_config) as logger:
        endTime = time.time() + 10
        for log_entry in logger:
            data = log_entry[1]
            currentPos[num] = data['stateEstimate.z']
            while currentPos[0] == 0 or currentPos[1] == 0 or currentPos[2] == 0:
                time.sleep(0.001)
                print('wait')
            if num == 0:
                consensus(currentPos)
            while nextPos[0] == 0 or nextPos[1] == 0 or nextPos[2] == 0:
                time.sleep(0.001)
                print('wait2')
            print(nextPos[num])
            poshold(cf,1,nextPos[num])
            if time.time() > endTime:
                break

    poshold(cf,2, end)
    # # Base altitude in meters
    #print(currentPos)
    #poshold(cf, 2, base)
    cf.commander.send_stop_setpoint()


if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)

    factory = CachedCfFactory(rw_cache='./cache')

    with Swarm(uris, factory=factory) as swarm:
        swarm.parallel(reset_estimator)
      # swarm.parallel(height_log)
        swarm.parallel(run_sequence, args_dict=params)
