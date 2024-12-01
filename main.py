# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 20:26:13 2023

Dependencies:
    Pandasgui - need to fix
        C:/Users/ericd/anaconda3/Lib/site-packages/pandasgui/utility.py
        Change bokeh.plotting.Figure to bokeh.plotting.figure  (lower case figure)
        This is used for the pandas dataframe GUI
    pyproj - used for translating map coords to lat,long coords

    Not currently used:
        selenium - used to click download button on Anderson website

@author: ericd
"""

import tkinter as tk
import tkinter.ttk as ttk
from pandasgui import show
import sys
import importlib
from datetime import datetime
import ast
import warnings
from Utils.gis_utils.county_driver import *
from Utils.County_Class import CountyClass
from Utils.google_util import find_distance
from Utils.tax_util import print_text, get_type
import qt_ui




########################################################
# GUI Portion of code
########################################################

########################################################
# Print Section
########################################################

pwin = tk.Text(master=frm_print, height=11, wrap='none')
ys = ttk.Scrollbar(master=frm_print, orient='vertical', command=pwin.yview)
pwin['yscrollcommand'] = ys.set

pwin.pack(fill=tk.X, side=tk.LEFT, expand=True)
ys.pack(fill=tk.Y, side=tk.RIGHT)

pwin.insert('1.0', 'Status messages will be printed here \n')
pwin['state'] = 'disabled'

