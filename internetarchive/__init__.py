# -*- coding: utf-8 -*-
"""
Internetarchive Library
~~~~~~~~~~~~~~~~~~~~~~~

Internetarchive is a python interface to archive.org.
usage:

    >>> import internetarchive
    >>> item = internetarchive.Item('govlawgacode20071')
    >>> item.exists
    True

:copyright: (c) 2013 by Jacob M. Johnson.
:license: GPL, see LICENSE for more details.

"""

__title__ = 'internetarchive'
__version__ = '0.5.0'
__author__ = 'Jacob M. Johnson'
__license__ = 'GPL'
__copyright__ = 'Copyright 2013 Jacob M. Johnson'

from .api import (
    get_item, get_file, get_files, download, modify_metadata, upload, delete, get_tasks,
    get_data_miner
)
