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

import pandas as pd
from pandasgui import show
from glob import glob
import os
import sys
import importlib
import datetime
import ast
import time
from Utils.County_Class import CountyClass
from Utils.google_util import find_distance
from Utils.tax_util import print_text, get_type
from PyQt6 import QtWidgets, uic
import qt_ui


class MainWindow(QtWidgets.QMainWindow, qt_ui):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()


