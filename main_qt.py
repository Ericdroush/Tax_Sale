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
from PyQt6.QtCore import Qt, QAbstractTableModel, QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QDialog, QTableView, QVBoxLayout
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QDialogButtonBox, QStyledItemDelegate, QStyle, QStyleOption
# from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from qt_ui import Ui_QMainWindow


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.color_enabled = True
        self.color_back = Qt.GlobalColor.magenta
        self.target_row = -1

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
            if role == Qt.ItemDataRole.BackgroundRole:
                if index.row() % 2 == 0:
                    return QBrush(QColor(235, 235, 235))
            # if role == Qt.ItemDataRole.BackgroundRole:
            #     print(1)
            #     return QBrush()
            # if role == Qt.ItemDataRole.BackgroundRole:
            #     print(index.row())
            #     print(self.color_enabled)
            #     # if index.row() == self.target_row and self.color_enabled is True:
            #     return QBrush(self.color_back)
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole:
            try:
                self._data.iloc[index.row(), index.column()] = value
                self.dataChanged.emit(index, index)
                return True
            except:
                return False
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(self._data.index[section])
        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(by=self._data.columns[column], ascending=order == Qt.SortOrder.AscendingOrder, inplace=True)
        self.layoutChanged.emit()


class CustomDialog(QDialog):
    def __init__(self, county, props, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.setWindowTitle("County Property Detail Viewer")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        self.table_view = QTableView()
        self.model = PandasModel(props)
        self.table_view.setModel(self.model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setStyleSheet("QTableView::item:selected{background:rgb(12, 128, 220)}")

        hidden_cols = [2, 6, 7, 10, 22, 23, 24, 28, 29, 30]  # Base hidden columns
        hidden_cols.extend([14, 15, 16, 18, 26, 27])
        for col in hidden_cols:
            self.table_view.hideColumn(col)

        pic_width = 300
        pic_height = int(pic_width * 2/3)
        self.selection_model = self.table_view.selectionModel()
        self.selection_model.selectionChanged.connect(lambda: self.update_pictures(county))
        # self.selection_model.selectionChanged.connect(self.highlight_row)

        self.v_layout = QVBoxLayout()
        self.h_layout_table = QHBoxLayout()
        self.h_layout_table.addWidget(self.table_view)

        self.h_layout_photos = QHBoxLayout()

        self.image_label = QLabel(self)
        pixmap = QPixmap('Counties/' + county + '/MapView/test.jpg')
        self.image_label.setPixmap(pixmap.scaled(pic_width, pic_height))
        self.h_layout_photos.addWidget(self.image_label)

        self.image_label1 = QLabel(self)
        pixmap = QPixmap('Counties/' + county + '/MapWideView/test.jpg')
        self.image_label1.setPixmap(pixmap.scaled(pic_width, pic_height))
        self.h_layout_photos.addWidget(self.image_label1)

        self.image_label2 = QLabel(self)
        pixmap = QPixmap('Counties/' + county + '/StreetView/test.jpg')
        self.image_label2.setPixmap(pixmap.scaled(pic_width, pic_height))
        self.h_layout_photos.addWidget(self.image_label2)

        self.image_label3 = QLabel(self)
        pixmap = QPixmap('Counties/' + county + '/CountyView/test.jpg')
        self.image_label3.setPixmap(pixmap.scaled(pic_width, pic_height))
        self.h_layout_photos.addWidget(self.image_label3)
        self.h_layout_photos.setSpacing(20)

        self.h_layout_captions = QHBoxLayout()
        url_link = '<a href="https://www.google.com/maps/">Google Maps</a>'
        self.label = QLabel(self)
        self.label.setText(url_link)
        self.label.setOpenExternalLinks(True)
        self.h_layout_captions.addWidget(self.label)

        self.label1 = QLabel(self)
        self.label1.setText(url_link)
        self.label1.setOpenExternalLinks(True)
        self.h_layout_captions.addWidget(self.label1)

        self.label2 = QLabel(self)
        self.label2.setText(url_link)
        self.label2.setOpenExternalLinks(True)
        self.h_layout_captions.addWidget(self.label2)

        url_link = '<a href="https://www.gcgis.org/apps/GreenvilleJS/">GCGIS</a>'
        self.label3 = QLabel(self)
        self.label3.setText(url_link)
        self.label3.setOpenExternalLinks(True)
        self.h_layout_captions.addWidget(self.label3)
        self.h_layout_captions.setSpacing(20)

        q_btn = (QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close)

        self.buttonBox = QDialogButtonBox(q_btn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.v_layout.addLayout(self.h_layout_table)
        self.v_layout.addLayout(self.h_layout_photos)
        self.v_layout.addLayout(self.h_layout_captions)
        self.v_layout.addWidget(self.buttonBox)
        self.v_layout.setContentsMargins(5, 5, 5, 5)
        self.v_layout.setSpacing(20)

        self.setLayout(self.v_layout)

    def update_pictures(self, county):
        indexes = self.table_view.selectedIndexes()
        if indexes:
            index = indexes[0]
            tax_map = index.siblingAtColumn(1).data()
            address = index.siblingAtColumn(4).data()
        else:
            return

        pic_width = int((self.width() - 40) / 4 - 10)
        pic_height = int(pic_width * 2/3)

        self.pen = QPen(Qt.GlobalColor.red)
        self.pen.setWidth(5)

        pixmap = QPixmap('Counties/' + county + '/MapView/' + str(tax_map) + '.jpg')
        self.painter_instance = QPainter(pixmap)
        self.painter_instance.setPen(self.pen)
        self.painter_instance.drawEllipse(300, 200, 10, 10)
        self.painter_instance.end()
        self.image_label.setPixmap(pixmap.scaled(pic_width, pic_height))
        link_address = ('https://www.google.com/maps/place/' +
                        address.split()[0].replace('+', '%2B') + ',+' +
                        address.split(',')[0].split()[1].replace(' ', '+') + ',+' +
                        address.split(',')[1].strip())
        url_link = '<a href="' + link_address + '">Google Maps</a>'
        self.label.setText(url_link)

        pixmap = QPixmap('Counties/' + county + '/MapWideView/' + str(tax_map) + '.jpg')
        self.painter_instance = QPainter(pixmap)
        self.painter_instance.setPen(self.pen)
        self.painter_instance.drawEllipse(300, 200, 10, 10)
        self.painter_instance.end()
        self.image_label1.setPixmap(pixmap.scaled(pic_width, pic_height))
        self.label1.setText(url_link)

        pixmap = QPixmap('Counties/' + county + '/StreetView/' + str(tax_map) + '.jpg')
        self.image_label2.setPixmap(pixmap.scaled(pic_width, pic_height))
        self.label2.setText(url_link)

        pixmap = QPixmap('Counties/' + county + '/CountyView/' + str(tax_map) + '.png')
        self.painter_instance = QPainter(pixmap)
        self.painter_instance.setPen(self.pen)
        self.painter_instance.drawEllipse(300, 200, 10, 10)
        self.painter_instance.end()
        self.image_label3.setPixmap(pixmap.scaled(pic_width, pic_height))
        url_link = '<a href="https://www.gcgis.org/apps/GreenvilleJS/?PIN=' + tax_map + '">GCGIS</a>'
        self.label3.setText(url_link)

        return

    # def highlight_row(self, selected, deselected):
    #     for index in selected.indexes():
    #         print(index.row())
    #         for col in range(self.model.columnCount()):
    #             item = self.model.data(index, Qt.ItemDataRole.BackgroundRole)
    #             print(item)
    #             if item:
    #                 item.setBackground(Qt.GlobalColor.yellow)
    #
    #     for index in deselected.indexes():
    #         print(index.row())
    #         for col in range(self.model.columnCount()):
    #             item = self.model.data(index, Qt.ItemDataRole.BackgroundRole)
    #             print(item)
    #             if item:
    #                 item.setBackground(Qt.GlobalColor.white)

    # def open_link(self, event, url):
    #     url = QUrl(url)
    #     QWebEngineView.openUrl(url)


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
        self.pushButton_pictures.clicked.connect(self.find_pictures)
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
                      'Pictures Found: ' + str(c1.pics_found) + '\n' +
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
        props_gui = props[props['withdrawn'] == 'A']
        props_withdrawn = props[props['withdrawn'] == 'W']
        county = self.combo_county.currentText()
        dlg = CustomDialog(county, props_gui)
        result = dlg.exec()
        if result == 1:  # Accepted, aka Save
            props_gui['rating'] = pd.to_numeric(props_gui['rating'], errors='coerce')
            self.count_rated(props_gui)
            props = pd.concat([props_gui, props_withdrawn], ignore_index=True)
            props.to_csv(self.get_filename(), index=False, na_rep='NaN')
            self.print_text('Properties have been successfully saved')

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

    def find_pictures(self):
        self.print_text('Downloading Pictures...')
        current_county = self.combo_county.currentText().lower()
        props = pd.read_csv(self.get_filename(), sep=',', dtype=get_type())

        t0 = time.perf_counter()
        dt = []
        count = 0
        total_count = len(props)
        for index, row in props.iterrows():
            count += 1
            t1 = time.perf_counter()
            dt.append(t1 - t0)
            t0 = t1
            est_time_left = sum(dt) / len(dt) * (total_count - count)
            self.print_text('Downloading pictures from google and county website for property {0}/{1}: '
                            'Estimated time remaining = {2}s'
                            .format(str(count), str(total_count), int(est_time_left)))
            bbox = row['bbox']
            taxmap = row['taxmap']
            loc = row['address']

            if isinstance(bbox, str):  # NaN will be a float, expecting a string
                get_county_pictures(taxmap, current_county, bbox)

            get_mapview(taxmap, current_county, loc)
            get_streetview(taxmap, current_county, loc)

        c[current_county].pics_found = True
        self.update_status()
        self.print_text('Done updating...')

    def delete_data(self):
        current_county = self.combo_county.currentText().lower()
        c[current_county] = CountyClass(current_county)
        os.remove(self.get_filename())
        self.set_btn_get_info_color(1)

        self.print_text('Data erased for ' + current_county)

    def print_text(self, inp):
        self.textBrowser_print.append(str(inp))
        QApplication.processEvents()


########################################################
# Main Code
########################################################
# Ignore the warnings about SSL calls to county websites
warnings.filterwarnings("ignore")

counties_list = get_counties()

c = {}
for county in counties_list:
    # mod = importlib.import_module('Utils.gis_utils.' + county, package=None)
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
            c[c1].pics_found = line['pics_found']
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

