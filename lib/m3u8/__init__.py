# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import logging
import os
import sys

from .httpclient import DefaultHTTPClient, _parsed_url
from .model import (M3U8, Segment, SegmentList, PartialSegment,
                        PartialSegmentList, Key, Playlist, IFramePlaylist,
                        Media, MediaList, PlaylistList, Start,
                        RenditionReport, RenditionReportList, ServerControl,
                        Skip, PartInformation, PreloadHint, DateRange,
                        DateRangeList)
from .parser import parse, is_url, ParseError


__all__ = ('M3U8', 'Segment', 'SegmentList', 'PartialSegment',
            'PartialSegmentList', 'Key', 'Playlist', 'IFramePlaylist',
            'Media', 'MediaList', 'PlaylistList', 'Start', 'RenditionReport',
            'RenditionReportList', 'ServerControl', 'Skip', 'PartInformation',
            'PreloadHint' 'DateRange', 'DateRangeList', 'loads', 'load',
            'parse', 'ParseError')

LOGGER = None

def loads(content, uri=None, custom_tags_parser=None):
    '''
    Given a string with a m3u8 content, returns a M3U8 object.
    Optionally parses a uri to set a correct base_uri on the M3U8 object.
    Raises ValueError if invalid content
    '''
    global LOGGER
    if LOGGER is None:
        LOGGER = logging.getLogger(__name__)
    if not content.startswith('#EXTM3U'):
        LOGGER.warning('INVALID m3u format: #EXTM3U missing {}'.format(uri))
        return None
    if uri is None:
        return M3U8(content, custom_tags_parser=custom_tags_parser)
    else:
        base_uri = _parsed_url(uri)
        return M3U8(content, base_uri=base_uri, custom_tags_parser=custom_tags_parser)


def load(uri, timeout=9, headers={}, custom_tags_parser=None, http_client=DefaultHTTPClient(), verify_ssl=True, http_session=None):
    '''
    Retrieves the content from a given URI and returns a M3U8 object.
    Raises ValueError if invalid content or IOError if request fails.
    '''
    global LOGGER
    if LOGGER is None:
        LOGGER = logging.getLogger(__name__)
    if is_url(uri):
        content, base_uri = http_client.download(uri, timeout, headers, verify_ssl, http_session)
        if content is None:
            LOGGER.warning('Unable to obtain m3u file {}'.format(uri))
            return None        
        if not content.startswith('#EXTM3U'):
            LOGGER.warning('INVALID m3u format: #EXTM3U missing {}'.format(uri))
            return None
        return M3U8(content, base_uri=base_uri, custom_tags_parser=custom_tags_parser)
    else:
        return _load_from_file(uri, custom_tags_parser)


def _load_from_file(uri, custom_tags_parser=None):
    global LOGGER
    if LOGGER is None:
        LOGGER = logging.getLogger(__name__)
    with open(uri, encoding='utf8') as fileobj:
        raw_content = fileobj.read().strip()
    base_uri = os.path.dirname(uri)
    if not raw_content.startswith('#EXTM3U'):
        LOGGER.warning('INVALID m3u format: #EXTM3U missing {}'.format(uri))
        return None
    return M3U8(raw_content, base_uri=base_uri, custom_tags_parser=custom_tags_parser)
