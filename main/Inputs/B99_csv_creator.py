import sys
import xml.etree.ElementTree as ET ## import xml parser
import os
import csv
import subprocess
try:
    from Inputs import PiUber
except:
    from TPITracker.Inputs import PiUber
from os.path import expanduser
import re
from .resource_path import resource_path

# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
#     base_path = re.sub(r"Inputs+$","",base_path,flags=re.I); #RC replaced split with regex to remove Inputs folder from folder path (avoid losing the I on I drive.)
#     return os.path.join(base_path, relative_path)


def B99_csv_creator(old_TP,new_TP,newnew_TP,site,wfr_coord):
    # This function pulls together all our B99 info
    home = expanduser("~");
    header_path = os.getcwd();

    sql_orig = resource_path("sql_files\\B99_pull.txt");
    #sql_new = header_path + "\\generated_files\B99_pull.txt";
    sql_new = header_path + "\\generated_files\all_B99_pull.txt";
    B99_raw_sql = header_path + "\\generated_files\\B99_raw_pull.csv";

    B99_sql_pull(old_TP,new_TP,newnew_TP,sql_orig,sql_new,B99_raw_sql,site,wfr_coord);

def B99_csv_creator(old_TP,new_TP,newnew_TP,site):
    # This function pulls together all our B99 info
    home = expanduser("~");
    header_path = os.getcwd();

    #sql_orig = resource_path("Inputs\sql_files\B99_pull.txt");
    sql_orig = resource_path("sql_files\\all_B99_pull.txt");
    sql_new = header_path + "\\generated_files\B99_pull.txt";
    B99_raw_sql = header_path + "\\generated_files\\B99_raw_pull.csv";

    B99_sql_pull(old_TP,new_TP,newnew_TP,sql_orig,sql_new,B99_raw_sql,site);

def B99_sql_pull(old_TP,new_TP,newnew_TP,sql_orig,sql_new,B99_raw_sql,site,wfr_coord):    
    # # edit SQL
    operation_list = ['\'' + str(old_TP.op) + '\'','\'' + str(new_TP.op) + '\'','\'' + str(newnew_TP.op) + '\''] #list of operations
    eng_IDs_list = ['\'' + str(old_TP.engID) + '\'','\'' + str(new_TP.engID) + '\'','\'' + str(newnew_TP.engID) + '\''] # list of Eng IDs three
 
    format_operations = (','.join(map(str, operation_list))) ## format operations list
    format_eng_IDs = (','.join(map(str, eng_IDs_list))) ## format Eng ID list
 
    with open(sql_orig, 'r') as file : # Read in the default sql script
      uber_script = file.read()
 
    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the operations
    uber_script = uber_script.replace('##OPERATIONS##',format_operations )# Replace the eng_id_list
    uber_script = uber_script.replace('##WFR_COORD##',wfr_coord )# Replace the WFR_COORD to pull historical data
 
    with open(sql_new, 'w') as file: # Write the file out again
      file.write(uber_script)
 
    ## run sql script
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site)); ## Selecting correct site
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(B99_raw_sql);
    print("B99 sql pull created");

    return()

def B99_sql_pull(old_TP,new_TP,newnew_TP,sql_orig,sql_new,B99_raw_sql,site):    
    # # edit SQL
    operation_list = ['\'' + str(old_TP.op) + '\'','\'' + str(new_TP.op) + '\'','\'' + str(newnew_TP.op) + '\''] #list of operations
    eng_IDs_list = ['\'' + str(old_TP.engID) + '\'','\'' + str(new_TP.engID) + '\'','\'' + str(newnew_TP.engID) + '\''] # list of Eng IDs three

    format_operations = (','.join(map(str, operation_list))) ## format operations list
    format_eng_IDs = (','.join(map(str, eng_IDs_list))) ## format Eng ID list

    with open(sql_orig, 'r') as file : # Read in the default sql script
      uber_script = file.read()

    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the operations
    uber_script = uber_script.replace('##OPERATIONS##',format_operations )# Replace the eng_id_list
    #uber_script = uber_script.replace('##WFR_COORD##',wfr_coord )# Replace the WFR_COORD to pull historical data

    with open(sql_new, 'w') as file: # Write the file out again
      file.write(uber_script)

    ## run sql script
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site)); ## Selecting correct site
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(B99_raw_sql);
    print("B99 sql pull created");

    return()
