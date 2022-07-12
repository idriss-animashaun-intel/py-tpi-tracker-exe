import sys
import xml.etree.ElementTree
import os
import csv
import subprocess
from os.path import expanduser
import itertools
import operator

python_exe = sys.executable

try:
    import pandas

except:
    print("need to import pandas")
    subprocess.call(python_exe +' Inputs/pip/get-pip.py --proxy="http://proxy-chain.intel.com:911"')
    import pip
    try:
        subprocess.call(python_exe + ' -m pip uninstall pandas')
        subprocess.call(python_exe + ' -m pip uninstall numpy')
    
    except:
        print("pandas/numpy not found")

    subprocess.call(python_exe + ' -m pip install pandas --proxy="http://proxy-chain.intel.com:911"')
    subprocess.call(python_exe + ' -m pip install numpy --proxy="http://proxy-chain.intel.com:911"')
    #print("Done installing pandas")
    import numpy
    import pandas

if sys.version_info >= (3,0,0):
    from tkinter import *
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import filedialog
else:
    from Tkinter import *
    import ttk
    import tkMessageBox
    import Tkconstants, tkFileDialog

#TPI_Tracker = "C:\\Users\\eoinbrad\\Source\\Repos\\TPI_Tracker\\15P_CLP_TPI_TRACKER_OUTPUT.xlsx"

def __init__():
    letsgo=1;

def post_build_integrity_check(TPI_Tracker):
    print("Running Audit of Tracker Output")  
    Tracker_DF = pandas.read_excel(TPI_Tracker, sheet_name='Raw_Data')
    col_vals = Tracker_DF.Wafer_id.unique()
    try:
        col_vals[1:].astype(int)

        if len(col_vals) < 2:
            print("There are not enough wafer in your TPI tracker - please review TPI Tracker Output")
            messagebox.showerror("Error", "There are not enough wafers in your TPI tracker - please review TPI Tracker Output")

        else:
            print("Audit successful")

    except ValueError:
        print("Error in wafers numbers - Data is corrupted - Please review TPI Tracker Output")
        messagebox.showerror("Error", "Error in wafers numbers - Data is corrupted - Please review TPI Tracker Output")
    
#post_build_integrity_check(TPI_Tracker)