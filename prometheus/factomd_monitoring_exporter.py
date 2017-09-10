#!/usr/bin/env python

import datetime
import time
import requests
import argparse

import os
from sys import exit
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

DEBUG = int(os.environ.get('DEBUG', '0'))

# addresses of follower instances used in various checks
TARGETS = {
         "t1": "http://courtesy-node.factom.com/v2",
         "t2": "http://courtesy-node.factom.com/v2",
         "t3": "http://courtesy-node.factom.com/v2"
        }

# The json payload for the heights command
HEIGHTS_PAYLOAD = '{"jsonrpc": "2.0", "id": 0, "method": "heights"}'

# The Header needed by the API call
FACTOMD_HEADERS = {
                    'Content-Type': 'text/plain'
                  }

# The Block time in seconds + 1 extra minute to "play safe"
BLOCK_SCAN_TIME = 60 * 11


class FactomdMonitoringCollector(object):
    # The build statuses we want to export .
    statuses = ["leader_directory_block", "follower_directory_block"]

    def __init__(self):
        self._leader_height = 0
        self._timestamp = time.time()

    def collect(self):
        # Request data from the Factomd Monitoring Collector
        heights = request_data()

        self._setup_empty_prometheus_metrics()

        if DEBUG:
            for height in heights:
                print("Found Height: {0}").format(height)

        self._get_metrics(heights)

        for status in self.statuses:
            for metric in self._prometheus_metrics[status].values():
                yield metric

        yield self._prometheus_metrics['success']

    def _setup_empty_prometheus_metrics(self):
        # The metrics we want to export.
        self._prometheus_metrics = {}
        for status in self.statuses:
            self._prometheus_metrics[status] = {
                'number':
                    GaugeMetricFamily('factomd_monitoring_{0}_count'.format(status),
                                      'Factomd monitoring height for {0}'.format(status), labels=['node']),
                'timestamp':
                    GaugeMetricFamily('factomd_monitoring_{0}_timestamp_seconds'.format(status),
                                      'Factomd Monitoring timestamp in unixtime for {0}'.format(status),
                                      labels=['node'])
            }
        self._prometheus_metrics['success'] = GaugeMetricFamily('factomd_monitoring_success',
                                                                'Factomd Monitoring success', labels=[])

    def _get_metrics(self, heights):
        _stall = 1
        _leader_dict = {}
        _follower_dict = {}
        for height in heights:
            # Bucket the leader heights
            if height['leader_directory_block'] in _leader_dict.keys():
                _leader_dict[height['leader_directory_block']] += 1
            else:
                _leader_dict[height['follower_directory_block']] = 1

            # Bucket the follower heights
            if height['follower_directory_block'] in _follower_dict.keys():
                _follower_dict[height['follower_directory_block']] += 1
            else:
                _follower_dict[height['follower_directory_block']] = 1

        # Sort the heights
        _bucketed_leader_heights_by_size = sorted(_leader_dict.items(), key=lambda x: x[0], reverse=True)
        _bucketed_leader_heights_by_count = sorted(_leader_dict.items(), key=lambda x: x[1], reverse=True)
        _bucketed_follower_heights_by_size = sorted(_follower_dict.items(), key=lambda x: x[0], reverse=True)
        _bucketed_follower_heights_by_count = sorted(_follower_dict.items(), key=lambda x: x[1], reverse=True)

        _max_leader_height = _bucketed_leader_heights_by_size[0][0]
        _max_leader_count = _bucketed_leader_heights_by_count[0][1]
        _max_count_leader_height = _bucketed_leader_heights_by_count[0][0]

        _max_follower_height = _bucketed_follower_heights_by_size[0][0]
        _max_follower_count = _bucketed_follower_heights_by_count[0][1]
        _max_count_follower_height = _bucketed_follower_heights_by_count[0][0]

        #
        # Stall conditions for leaders
        #

        # If the highest leader is behind the last scan, then STALLED
        if _max_leader_height < self._leader_height:
            _stall = 0

        # If >50% of the leaders are behind the last scan, then STALLED
        if _max_leader_count > int(len(heights)/2):
            if _max_count_leader_height < self._leader_height:
                _stall = 0

        # If BLOCK_SCAN_TIME has passed, and the leader height is the same or less, then STALLED
        if time.time() - (self._timestamp + BLOCK_SCAN_TIME) > 0:
            if _max_leader_height <= self._leader_height:
                _stall = 0

        #
        # Stall conditions for followers
        #

        # If the highest follower is more than two behind, then STALLED
        if _max_follower_height < _max_leader_height - 1:
            _stall = 0

        # If >50% of the followers are behind the last scan, then STALLED
        if _max_follower_count > int(len(heights)/2):
            if _max_count_follower_height < _max_leader_height - 1:
                _stall = 0

        #
        # Store any changed params
        #
        if DEBUG:
            print("time_diff {0}, old_height {1}, max_height {2}").format(int(time.time() - self._timestamp),
                                                                          self._leader_height,
                                                                          _max_leader_height)

        # Initialization
        if self._leader_height == 0:
            self._leader_height = _max_leader_height

        # If we haven't stalled, then update statii, but only if BLOCK_SCAN_TIME has passed
        if time.time() >= (self._timestamp + BLOCK_SCAN_TIME):
            self._leader_height = _max_leader_height
            self._timestamp = time.time()
        # Else, if >50% of the followers are reporting a height increase
        #   then we are probably misaligned with the block-time, so go ahead and update the status
        elif _max_leader_count > int(len(heights)/2):
            if _max_count_leader_height > self._leader_height:
                self._leader_height = _max_leader_height
                self._timestamp = time.time()

        self._prometheus_metrics['success'].add_metric([], int(_stall))

        for height in heights:
            for status in self.statuses:
                if status in height.keys():
                    status_data = height[status] or 0
                    target = height['target']
                    self._add_data_to_prometheus_structure(status, status_data, target)

    def _add_data_to_prometheus_structure(self, status, status_data, target):
        # If there's a null result, we want to pass.
        self._prometheus_metrics[status]['number'].add_metric([target], int(status_data))
        self._prometheus_metrics[status]['timestamp'].add_metric([target], int(time.time()))


def request_data():

    def parse_height(dest):
        url = '{0}'.format(TARGETS[dest])
        response = requests.post(url, headers=FACTOMD_HEADERS, data=HEIGHTS_PAYLOAD)
        if response.status_code != requests.codes.ok:
            return[]
        result = response.json()

        _height = {
                    'leader_directory_block': result['result']['leaderheight'],
                    'follower_directory_block': result['result']['directoryblockheight'],
                    'dest': dest
                   }

        return _height

    # Request exactly the information we need from Factomd Monitoring
    heights = []
    for target in TARGETS:
        height = parse_height(target)
        heights.append(height)

    return heights


def parse_args():
    parser = argparse.ArgumentParser(
        description='Factomd Monitoring port'
    )

    parser.add_argument(
        '-p', '--port',
        metavar='port',
        required=False,
        type=int,
        help='Listen to this port',
        default=int(os.environ.get('VIRTUAL_PORT', '9119'))
    )
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        port = int(args.port)
        REGISTRY.register(FactomdMonitoringCollector())
        start_http_server(port)
        print("Serving at port: {0}").format(port)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)


if __name__ == "__main__":
    main()
