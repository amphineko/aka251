#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import shlex
import sys

import pynvml


async def dispatch(command, handle, index, interval):
    process = None
    while True:
        processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        if process is None:
            device = query_device(index)
            if len(processes) == 0:
                process = await asyncio.create_subprocess_exec(*command, stderr=sys.stderr, stdout=sys.stdout)
                print('Process started')
        else:
            if process.returncode is not None:
                print('ERROR: Process exited with return code %d' % process.returncode)
                process = None
                continue

            processes = list(
                filter(lambda p: p.pid != process.pid, pynvml.nvmlDeviceGetComputeRunningProcesses(handle)))
            if len(processes) > 0:
                print('Process terminated')
                process.terminate()
                process = None
        await asyncio.sleep(interval)


def parse_arguments():
    parser = argparse.ArgumentParser(description='NVIDIA device usage monitor and job dispatcher (not yet)')
    parser.add_argument('--command', '-c', default=None, dest='command', help='Command to execute', type=str)
    parser.add_argument('--index', '-i', default=-1, dest='device_index', help='Device index to monitor', type=int)
    parser.add_argument('--interval', '-I', default=5, dest='interval', help='Interval of monitoring', type=int)
    return parser.parse_args()


def query_device(index):
    handle = pynvml.nvmlDeviceGetHandleByIndex(index)
    return {
        'index': index,
        'name': pynvml.nvmlDeviceGetName(handle).decode(),
        'utilization': pynvml.nvmlDeviceGetUtilizationRates(handle).gpu,
        'uuid': pynvml.nvmlDeviceGetUUID(handle).decode(),
    }


if __name__ == '__main__':
    pynvml.nvmlInit()

    try:
        print('NVIDIA Driver version %s' % pynvml.nvmlSystemGetDriverVersion().decode())
        print('NVML API %s initialized' % pynvml.nvmlSystemGetNVMLVersion().decode())
        print()

        config = parse_arguments()

        device_count = pynvml.nvmlDeviceGetCount()
        devices = [query_device(i) for i in range(0, device_count)]

        if not (config.device_index in range(0, device_count)):
            print('Available devices:')
            list(map(lambda device: print(
                'Device #%d:\t%s\t%d%%\t%s' % (device['index'], device['name'], device['utilization'], device['uuid'])),
                     devices))
            exit(1)

        if config.command is None:
            print('ERROR: Command is required')
            exit(1)

        loop = asyncio.get_event_loop()
        print(shlex.split(config.command))
        task = asyncio.ensure_future(
            dispatch(shlex.split(config.command), pynvml.nvmlDeviceGetHandleByIndex(config.device_index),
                     config.device_index, config.interval))

        loop.run_forever()
    finally:
        pynvml.nvmlShutdown()
