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
import pandas as pd
from pandasgui import show
from glob import glob
import os
import sys
import importlib
import datetime
import ast
import time
from Tests import CountyClass
from Tests import find_distance
from Tests import print_text, get_type

counties_list = [x.split('\\')[1].rstrip('.py') for x in glob('Utils/gis_utils/*.py')]

#import Utils.gis_utils.greenville
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


########################################################
# Functions
########################################################
def write_init_file():
    with open('datafile.txt', 'w') as f:
        f.write(combo_county.get() + '\n')
        for c_county, c_class in c.items():
            f.write(str(vars(c_class)) + '\n')


def get_filename():
    return 'Counties/' + combo_county.get() + '/props.csv'


def count_rated(df):
    c[combo_county.get().lower()].rated = df['rating'].count()
    c[combo_county.get().lower()].rated_high = df['rating'][df['rating'] >= 3].count()
    update_status()
    return


def read_props():
    df = pd.read_csv(get_filename(), dtype=get_type())
    count_rated(df)
    print_text(pwin, 'Properties have been read in for ' + combo_county.get() + ' County')
    return df


def show_gui():
    props = read_props()
    print_text(pwin, 'Starting gui...')
    gui = show(props)
    #, settings={'theme':'dark'}
    # Code pauses while the gui is open
    props_new = gui['props']
    count_rated(props_new)
    props_new.to_csv(get_filename(), index=False, na_rep='NaN')


def set_btn_get_info_color(*args):
    if os.path.isfile(get_filename()):
        btn_get_info.config(bg='GREEN')
    else:
        btn_get_info.config(bg='SystemButtonFace')

    update_status()


def main_get_property_info():
    print_text(pwin, 'Retrieving property GIS information...')
    print_text(pwin, ' * * *  This may take a while * * * ')
    c[combo_county.get().lower()].orig_count = (
        sys.modules['Utils.gis_utils.' + combo_county.get().lower()].get_gis_info(pwin, get_filename(), test_flag))
    c[combo_county.get().lower()].count = c[combo_county.get().lower()].orig_count
    c[combo_county.get().lower()].props_exist = True
    c[combo_county.get().lower()].last_updated = datetime.date.today().strftime('%m/%d/%Y')

    set_btn_get_info_color('')
    print_text(pwin, 'Done retrieving...')


def main_update_withdrawn():
    print_text(pwin, 'Updating currently available properties...')

    c[combo_county.get().lower()].count, c[combo_county.get().lower()].withdrawn_last = (
        sys.modules['Utils.gis_utils.' + combo_county.get().lower()].update_withdrawn(pwin, get_filename(), test_flag))
    c[combo_county.get().lower()].last_updated = datetime.date.today().strftime('%m/%d/%Y')

    update_status()
    print_text(pwin, 'Done updating...')


def calc_distance():

    print_text(pwin, 'Calculating distance from addresses...')
    d = [dest1.get(), dest2.get(), dest3.get()]
    c[combo_county.get().lower()].addr1 = d[0]
    c[combo_county.get().lower()].addr2 = d[1]
    c[combo_county.get().lower()].addr3 = d[2]

    destinations = []
    for dest in d:
        if not 'Enter Address' in dest:
            destinations.append(dest)
        else:
            destinations.append('')

    props = read_props()

    d1 = []
    d2 = []
    d3 = []
    t0 = time.perf_counter()
    dt = []
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
        print_text(pwin, 'Finding distane for property {0}/{1}:  Estimated time remaining = {2}s'
                   .format(str(count), str(total_count), str(est_time_left)))

    props['dist1'] = d1
    props['dist2'] = d2
    props['dist3'] = d3

    props.to_csv(get_filename(), index=False, na_rep='NaN')

    c[combo_county.get().lower()].distance_calcd = True
    update_status()
    print_text(pwin, 'Done finding distance...')


def find_lakes():
    print_text(pwin, 'Updating lake percentages...')

    c[combo_county.get().lower()].lakes_found = (
        sys.modules['Utils.gis_utils.' + combo_county.get().lower()].find_lake_props(pwin, get_filename()))

    update_status()
    print_text(pwin, 'Done updating...')


def update_status():
    c1 = c[combo_county.get().lower()]
    stats['state'] = 'normal'
    stats.delete("1.0","end-1c")

    stats.insert(tk.END, 'Status \n')
    stats.insert(tk.END, 'County: ' + combo_county.get() + '\n')
    stats.insert(tk.END, 'Properties Exist: ' + str(c1.props_exist) + '\n')
    stats.insert(tk.END, "Distanced Calc'd: " + str(c1.distance_calcd) + '\n')
    stats.insert(tk.END, 'Lakes Found: ' + str(c1.lakes_found) + '\n')
    stats.insert(tk.END, 'Last Updated: ' + c1.last_updated + '\n')
    stats.insert(tk.END, 'Count: ' + str(c1.count) + '\n')
    stats.insert(tk.END, '# Rated: ' + str(c1.rated) + '\n')
    stats.insert(tk.END, '# Highly Rated: ' + str(c1.rated_high) + '\n')
    stats.insert(tk.END, 'Original Count: ' + str(c1.orig_count) + '\n')
    stats.insert(tk.END, 'Withdrawn Recently: ' + str(c1.withdrawn_last) + '\n')

    stats['state'] = 'disabled'


def close_window():
    write_init_file()
    window.quit()


def delete_data():
    c[combo_county.get().lower()] = CountyClass(combo_county.get().lower())
    os.remove(get_filename())
    set_btn_get_info_color()

    print_text(pwin, 'Data erased for ' + combo_county.get())

def toggle_test():
    global test_flag
    if test_btn.config('relief')[-1] == 'sunken':
        test_btn.config(relief="raised")
        test_btn.config(bg='SystemButtonFace')
        test_flag = False

    else:
        test_btn.config(relief="sunken")
        test_btn.config(bg='RED')
        test_flag = True

    return test_flag


########################################################
# GUI Portion of code
########################################################

window = tk.Tk()
window.title("Tax Sale Property Screening Tool")

for i in range(4):
    window.columnconfigure(i, weight=1) #, minsize=75)

for i in range(4):
    window.rowconfigure(i, weight=1) #, minsize=50)

########################################################
# County Frame
########################################################
frm_county = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=3)
frm_county.grid(row=0, column=0,rowspan=2, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)

combo_county = ttk.Combobox(
    master=frm_county,
    state='readonly',
    values=[county.title() for county in counties_list],
)
combo_county.bind('<<ComboboxSelected>>', set_btn_get_info_color)
combo_county.set(default_county)

label = tk.Label(
    master=frm_county,
    text="County Selector",
    width=25,
    height=1
)

btn_get_info = tk.Button(
    master=frm_county,
    text="Get Property Info",
    width=25,
    height=1,
    command=main_get_property_info
)

btn_update_list = tk.Button(
    master=frm_county,
    text="Update List",
    width=25,
    height=1,
    command=main_update_withdrawn
)

btn_show_list = tk.Button(
    master=frm_county,
    text="Show List",
    width=25,
    height=1,
    command=show_gui
)

#County Frame Fill Options
combo_county.pack(fill=tk.X, side=tk.TOP, expand=True)
label.pack(fill=tk.X, side=tk.RIGHT, expand=True)
btn_get_info.pack(side=tk.TOP)
btn_update_list.pack(side=tk.TOP)
btn_show_list.pack(side=tk.TOP)

########################################################
# Distance Frame
########################################################
frm_distance = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=3)
frm_distance.grid(row=0, column=2, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)

label = tk.Label(
    master=frm_distance,
    text="Please Select Distance Options",
    width=100,
    height=2
)

if combo_county.get() == '':
    text1 = 'Enter Address 1'
    text2 = 'Enter Address 2'
    text3 = 'Enter Address 3'
else:
    text1 = c[combo_county.get().lower()].addr1
    text2 = c[combo_county.get().lower()].addr2
    text3 = c[combo_county.get().lower()].addr3

dest1 = tk.Entry(master=frm_distance, width=75)
dest1.insert(0, text1)
dest2 = tk.Entry(master=frm_distance, width=75)
dest2.insert(0, text2)
dest3 = tk.Entry(master=frm_distance, width=75)
dest3.insert(0, text3)

btn_distance = tk.Button(
    master=frm_distance,
    text="Calculate Distance",
    width=25,
    height=1,
    command=calc_distance
)


label.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
dest1.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
dest2.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
dest3.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
btn_distance.grid(row=0, column=2, rowspan=4, padx=5, pady=5)

########################################################
# Lake Frame
########################################################
frm_lake = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=3)
frm_lake.grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)

btn_lake = tk.Button(
    master=frm_lake,
    text="Find Lakes",
    width=25,
    height=1,
    command=find_lakes
)

btn_lake.pack(side=tk.TOP)

########################################################
# Print Section
########################################################
frm_print = tk.Frame(master=window, borderwidth=3)
frm_print.grid(row=3, column=0, columnspan=3, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)

pwin = tk.Text(master=frm_print, height=11, wrap='none')
ys = ttk.Scrollbar(master=frm_print, orient = 'vertical', command = pwin.yview)
pwin['yscrollcommand'] = ys.set

pwin.pack(fill=tk.X, side=tk.LEFT, expand=True)
ys.pack(fill=tk.Y, side=tk.RIGHT)

pwin.insert('1.0', 'Status messages will be printed here \n')
pwin['state'] = 'disabled'

########################################################
# Status Section
########################################################
frm_status = tk.Frame(master=window, borderwidth=3)
frm_status.grid(row=3, column=3, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)

stats = tk.Text(master=frm_status, width=30, height=11, background=window.cget('bg'), wrap='none')
stats.pack(fill=tk.X, side=tk.TOP, expand=True)

stats.insert(tk.END, 'Status \n')
stats['state'] = 'disabled'

########################################################
# Bottom Button Section
########################################################
ok_btn = tk.Button(
    text="Done",
    width=25,
    height=1,
    command=close_window
)
ok_btn.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

del_btn = tk.Button(
    text="Delete Data",
    width=25,
    height=1,
    command=delete_data
)
del_btn.grid(row=5, column=2, padx=5, pady=5)

set_btn_get_info_color() # Initializes the default county selection

test_btn = tk.Button(
    text="Test Mode",
    width=25,
    height=1,
    relief="raised",
    command=toggle_test
)
test_flag = False
test_btn.grid(row=5, column=3, padx=5, pady=5)

#################################################################
#   Events Section
#   https://web.archive.org/web/20190512164300/http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/event-types.html
#################################################################


window.mainloop()