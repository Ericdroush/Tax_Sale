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
import warnings
import sys
import importlib
import datetime
import ast
import time
from Utils.County_Class import CountyClass
from Utils.google_util import find_distance
from Utils.tax_util import *
from Utils.gis_utils.county_driver import *
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QDialog, QTableView, QVBoxLayout
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QDialogButtonBox
from qt_ui import Ui_QMainWindow
from list_dlg import Ui_List_Dialog


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                value = self._data.iloc[index.row(), index.column()]
                if index.column() == 8:  # Acres
                    value = "%.2f" % value
                else:
                    value = str(value)

                return value
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(self._data.index[section])
        return None


class CustomDialog(QDialog):
    def __init__(self, county, props, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.setWindowTitle("County Property Detail Viewer")
        # self.tableView.installEventFilter(self)

        table_view = QTableView()
        model = PandasModel(props)
        table_view.setModel(model)

        hidden_cols = [2, 6, 7, 10, 22, 23, 24, 28, 29, 30]
        for col in hidden_cols:
            table_view.hideColumn(col)

        selection_model = table_view.selectionModel()
        h_layout_photos = selection_model.selectionChanged.connect(table_view.selected_row, county)

        v_layout = QVBoxLayout()
        h_layout_table = QHBoxLayout()
        h_layout_table.addWidget(table_view)

        QBtn = (
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        v_layout.addLayout(h_layout_table)
        v_layout.addLayout(h_layout_photos)
        v_layout.addWidget(self.buttonBox)
        v_layout.setContentsMargins(5, 5, 5, 5)
        v_layout.setSpacing(20)

        self.setLayout(v_layout)

    def get_tax_map(self):
        indexes = self.table_view.selectedIndexes()
        if indexes:
            index = indexes[0]
            row = index.row()
            print(row)

    def update_pictures(self, tax_map, county):
        print(tax_map, county)
        h_layout_photos = QHBoxLayout()

        image_label = QLabel(self)
        pixmap = QPixmap('Counties/' + county + '/MapView/' + str(tax_map) + '.jpg')
        image_label.setPixmap(pixmap)
        h_layout_photos.addWidget(image_label)

        image_label2 = QLabel(self)
        pixmap = QPixmap('Counties/' + county + '/StreetView/' + str(tax_map) + '.jpg')
        image_label2.setPixmap(pixmap)
        h_layout_photos.addWidget(image_label2)

        image_label3 = QLabel(self)
        pixmap = QPixmap('Counties/' + county + '/StreetView/' + str(tax_map) + '.jpg')
        image_label3.setPixmap(pixmap)
        h_layout_photos.addWidget(image_label3)
        h_layout_photos.setSpacing(20)

        return h_layout_photos


class MainWindow(QMainWindow, Ui_QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Set County Combobox entries
        self.combo_county.addItems(county.title() for county in counties_list)
        self.combo_county.currentTextChanged.connect(self.set_btn_get_info_color)
        self.combo_county.currentTextChanged.connect(self.set_address_fields)
        self.combo_county.setCurrentText(default_county)

        # Button mapping
        self.pushButton_done.clicked.connect(self.close_window)
        self.pushButton_getinfo.clicked.connect(self.main_get_property_info)
        self.pushButton_update_list.clicked.connect(self.main_update_withdrawn)
        self.pushButton_Show_List.clicked.connect(self.show_gui)
        self.pushButton_distance.clicked.connect(self.calc_distance)
        self.pushButton_lakes.clicked.connect(self.find_lakes)
        self.pushButton_delete.clicked.connect(self.delete_data)

        # Call these to properly initialize the form - they won't get called if the default county is the first county
        # in the list as it won't trigger the "changed" signals
        self.set_btn_get_info_color(self.combo_county.currentText())
        self.set_address_fields(self.combo_county.currentText())

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage('Welcome to the Tax Sale Data Collector')
        self.progressBar = QtWidgets.QProgressBar()
        status_bar.addPermanentWidget(self.progressBar)
        self.progressBar.hide()

    def set_btn_get_info_color(self, text):
        # Could use text instead of get_filename, but for consistency keeping the function
        if os.path.isfile(self.get_filename()):
            self.pushButton_getinfo.setStyleSheet('background-color: green; ')
        else:
            self.pushButton_getinfo.setStyleSheet('')
        self.update_status()
        # QApplication.processEvents()

    def set_address_fields(self, text):
        text = text.lower()
        self.lineEdit_address1.setText(c[text].addr1)
        self.lineEdit_address2.setText(c[text].addr2)
        self.lineEdit_address3.setText(c[text].addr3)
        # QApplication.processEvents()

    def update_status(self):
        current_county = self.combo_county.currentText().lower()
        self.textBrowser_status.setPlaceholderText('')
        if current_county in c.keys():
            c1 = c[current_county]
            status = ('Status \n' +
                      'County: ' + current_county.title() + '\n' +
                      'Properties Exist: ' + str(c1.props_exist) + '\n' +
                      "Distanced Calc'd: " + str(c1.distance_calcd) + '\n' +
                      'Lakes Found: ' + str(c1.lakes_found) + '\n' +
                      'Last Updated: ' + c1.last_updated + '\n' +
                      'Count: ' + str(c1.count) + '\n' +
                      '# Rated: ' + str(c1.rated) + '\n' +
                      '# Highly Rated: ' + str(c1.rated_high) + '\n' +
                      'Original Count: ' + str(c1.orig_count) + '\n' +
                      'Withdrawn Recently: ' + str(c1.withdrawn_last) + '\n')

            self.textBrowser_status.setPlainText(status)

        else:
            # This loop will get his when there is no default county - typically during first time running
            self.textBrowser_status.setPlainText('')

        # QApplication.processEvents()
        return

    def update_progress(self):
        max_num = 1000000
        self.progressBar.show()
        self.progressBar.setRange(0, max_num)
        for i in range(max_num):
            i = i * 100 / 100 + 100 - 100
            self.progressBar.setValue(int(i))
        self.progressBar.hide()
        return

    def show_gui(self):
        self.print_text('Starting gui...')
        props = self.read_props()
        county = self.combo_county.currentText()
        dlg = CustomDialog(county, props)
        dlg.exec()

    def show_gui_old(self):
        props = self.read_props()
        self.print_text('Starting gui...')
        gui = show(props)
        # , settings={'theme':'dark'}
        # Code pauses while the gui is open
        props_new = gui['props']
        self.count_rated(props_new)
        props_new.to_csv(self.get_filename(), index=False, na_rep='NaN')

    def close_window(self):
        self.write_init_file()
        self.close()

    def write_init_file(self):
        with open('datafile.txt', 'w') as f:
            f.write(self.combo_county.currentText() + '\n')
            for c_county, c_class in c.items():
                f.write(str(vars(c_class)) + '\n')

    def get_filename(self):
        return 'Counties/' + self.combo_county.currentText() + '/props.csv'

    def count_rated(self, df):
        current_county = self.combo_county.currentText().lower()
        c[current_county].rated = df['rating'].count()
        c[current_county].rated_high = df['rating'][df['rating'] >= 3].count()
        self.update_status()
        return

    def read_props(self):
        df = pd.read_csv(self.get_filename(), dtype=get_type())
        self.count_rated(df)
        self.print_text('Properties have been read in for ' + self.combo_county.currentText() + ' County')
        return df

    def main_get_property_info(self):
        self.print_text('Retrieving property GIS information...')
        self.print_text(' * * *  This may take a while * * * ')
        current_county = self.combo_county.currentText().lower()
        c[current_county].orig_count = get_gis_info(
            self, current_county, self.get_filename(), self.checkBox_testmode.isChecked())
        c[current_county].count = c[current_county].orig_count
        c[current_county].props_exist = True
        c[current_county].last_updated = datetime.today().strftime('%m/%d/%Y')

        self.set_btn_get_info_color('')
        self.print_text('Done retrieving...')

    def main_update_withdrawn(self):
        self.print_text('Updating currently available properties...')
        current_county = self.combo_county.currentText().lower()
        c[current_county].count, c[current_county].withdrawn_last = \
            (update_withdrawn(self, current_county, self.get_filename(),
                              self.checkBox_testmode.isChecked()))
        c[current_county].last_updated = datetime.today().strftime('%m/%d/%Y')

        self.update_status()
        self.print_text('Done updating...')

    def calc_distance(self):
        self.print_text('Calculating distance from addresses...')
        current_county = self.combo_county.currentText().lower()
        c[current_county].addr1 = self.lineEdit_address1.text()
        c[current_county].addr2 = self.lineEdit_address2.text()
        c[current_county].addr3 = self.lineEdit_address3.text()
        destinations = [c[current_county].addr1, c[current_county].addr2, c[current_county].addr3]

        props = self.read_props()

        d1, d2, d3, dt = [], [], [], []
        t0 = time.perf_counter()
        count = 0
        total_count = len(props)
        for origin in props['address']:
            count += 1
            if origin == 'NaN':
                d1.append('NaN')
                d2.append('NaN')
                d3.append('NaN')
            else:
                dists = find_distance(origin, destinations)
                d1.append(dists[0])
                d2.append(dists[1])
                d3.append(dists[2])

            t1 = time.perf_counter()
            dt.append(t1 - t0)
            t0 = t1
            est_time_left = round(sum(dt) / len(dt) * (total_count - count), 0)
            self.print_text(
                       'Finding distance for property {0}/{1}:  Estimated time remaining = {2}s'
                       .format(str(count), str(total_count), str(est_time_left)))

        props['dist1'] = d1
        props['dist2'] = d2
        props['dist3'] = d3

        props.to_csv(self.get_filename(), index=False, na_rep='NaN')

        c[current_county].distance_calcd = True
        self.update_status()
        self.print_text('Done finding distance...')

    def find_lakes(self):
        self.print_text('Updating lake percentages...')
        current_county = self.combo_county.currentText().lower()
        c[current_county].lakes_found = find_lake_props(self, current_county, self.get_filename())
        self.update_status()
        self.print_text('Done updating...')

    def delete_data(self):
        current_county = self.combo_county.currentText().lower()
        c[current_county] = CountyClass(current_county)
        os.remove(self.get_filename())
        self.set_btn_get_info_color(1)

        self.print_text('Data erased for ' + current_county)

    def print_text(self, inp):
        self.textBrowser_print.append(str(inp) + '\n')
        QApplication.processEvents()


########################################################
# Main Code
########################################################
# Ignore the warnings about SSL calls to county websites
warnings.filterwarnings("ignore")

counties_list = get_counties()

c = {}
for county in counties_list:
    mod = importlib.import_module('Utils.gis_utils.' + county, package=None)
    c[county] = CountyClass(county)

# Read initialization data
if os.path.isfile('datafile.txt'):
    with open('datafile.txt') as f:
        init = f.readlines()

    default_county = init.pop(0).strip()
    for line in init:
        line = ast.literal_eval(line)
        c1 = line['name']
        if c1 in counties_list:
            c[c1].props_exist = line['props_exist']
            c[c1].addr1 = line['addr1']
            c[c1].addr2 = line['addr2']
            c[c1].addr3 = line['addr3']
            c[c1].distance_calcd = line['distance_calcd']
            c[c1].lakes_found = line['lakes_found']
            c[c1].last_updated = line['last_updated']
            c[c1].count = line['count']
            c[c1].rated = line['rated']
            c[c1].rated_high = line['rated_high']
            c[c1].orig_count = line['orig_count']
            c[c1].withdrawn_last = line['withdrawn_last']
else:
    default_county = ''


app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")
window = MainWindow()
window.show()
sys.exit(app.exec())

