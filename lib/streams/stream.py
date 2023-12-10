"""
MIT License

Copyright (C) 2021 ROCKY4546
https://github.com/rocky4546

This file is part of Cabernet

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.
"""

import logging

from lib.web.pages.templates import web_templates
from lib.clients.web_handler import WebHTTPHandler
import lib.common.utils as utils


class Stream:
    logger = None

    def __init__(self, _plugins, _hdhr_queue):
        self.plugins = _plugins
        self.namespace = ''
        self.instance = ''
        self.config = self.plugins.config_obj.data
        self.hdhr_queue = _hdhr_queue
        if Stream.logger is None:
            Stream.logger = logging.getLogger(__name__)

    def put_hdhr_queue(self, _namespace, _index, _channel, _status):
        if not self.config['hdhomerun']['disable_hdhr']:
            self.hdhr_queue.put(
                {'namespace': _namespace, 'tuner': _index,
                 'channel': _channel, 'status': _status})

    def find_tuner(self, _namespace, _instance, _ch_num, _isvod):
        # keep track of how many tuners we can use at a time
        found = -1
        scan_list = WebHTTPHandler.rmg_station_scans[_namespace]
        for index, scan_status in enumerate(scan_list):
            # the first idle tuner gets it
            if scan_status == 'Idle' and found == -1:
                found = index
            elif isinstance(scan_status, dict):
                if scan_status['instance'] == _instance \
                        and scan_status['ch'] == _ch_num \
                        and not _isvod \
                        and scan_status['mux'] \
                        and not scan_status['mux'].terminate_requested:
                    found = index
                    break
        if found == -1:
            return found
        if WebHTTPHandler.rmg_station_scans[_namespace][index] != 'Idle':
            self.logger.debug('Reusing tuner {} {}:{} ch:{}'.format(found, _namespace, _instance, _ch_num))
        else:
            self.logger.debug('Adding new tuner {} for stream {}:{} ch:{}'.format(found, _namespace, _instance, _ch_num))
            WebHTTPHandler.rmg_station_scans[_namespace][found] = { \
                'instance': _instance,
                'ch': _ch_num,
                'mux': None,
                'status': 'Starting'}
            self.put_hdhr_queue(_namespace, index, _ch_num, 'Stream')
        return found

    def set_service_name(self, _channel_dict):
        updated_chnum = utils.wrap_chnum(
            str(_channel_dict['display_number']), _channel_dict['namespace'],
            _channel_dict['instance'], self.config)

        if self.config['epg']['epg_channel_number']:
            service_name = updated_chnum + \
                           ' ' + _channel_dict['display_name']
        else:
            service_name = _channel_dict['display_name']
        return service_name

    def get_stream_uri(self, _channel_dict):
        return self.plugins.plugins[_channel_dict['namespace']] \
            .plugin_obj.get_channel_uri_ext(_channel_dict['uid'], _channel_dict['instance'])

    def gen_response(self, _namespace, _instance, _ch_num, _isvod):
        """
        Returns dict where the dict is consistent with
        the method do_dict_response requires as an argument
        A code other than 200 means do not tune
        dict also include a "tuner_index" that informs caller what tuner is allocated
        """
        self.namespace = _namespace
        self.instance = _instance
        i = self.find_tuner(_namespace, _instance, _ch_num, _isvod)
        if i >= 0:
            return {
                'tuner': i,
                'code': 200,
                'headers': {'Content-type': 'video/MP2T;'},
                'text': None}
        else:
            self.logger.warning(
                'All tuners already in use [{}][{}] max tuners: {}'
                .format(_namespace, _instance, len(WebHTTPHandler.rmg_station_scans[_namespace])))
            return {
                'tuner': i,
                'code': 400,
                'headers': {'Content-type': 'text/html'},
                'text': web_templates['htmlError'].format('400 - All tuners already in use.')}

    @property
    def config_section(self):
        return utils.instance_config_section(self.namespace, self.instance)
