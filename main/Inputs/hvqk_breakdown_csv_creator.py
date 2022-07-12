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


def hvqk_breakdown_csv_creator(old_TP,new_TP,newnew_TP,site,do_newnew):
    # This function pulls together all our vadtl info
    home = expanduser("~");
    header_path = os.getcwd();
    
    sql_orig = resource_path("sql_files\\hvqkVerbosePull.txt");
    sql_new = header_path + "\\generated_files\\hvqkVerbosePull.txt";
    hvqk_raw_sql = header_path+"\\Outputs\\hvqkVerbosePull.csv";
    
    HVQK_sql_pull(old_TP,new_TP,newnew_TP,sql_orig,sql_new,hvqk_raw_sql,site,do_newnew);


def HVQK_sql_pull(old_TP,new_TP,newnew_TP,sql_orig,sql_new,hvqk_raw_sql,site,do_newnew):    
    # This script does the thing

    operation_list = [];
    eng_IDs_list = [];
    
    # Create list of operations to be pulled
    operation_list = operation_list + ['\'' + str(old_TP.op) + '\''];
    operation_list = operation_list + ['\'' + str(new_TP.op) + '\''];
    if do_newnew:
        operation_list = operation_list + ['\'' + str(newnew_TP.op) + '\''];
        
    # Create list of engID's to be pulled
    eng_IDs_list = eng_IDs_list + ['\'' + str(old_TP.engID) + '\''];
    eng_IDs_list = eng_IDs_list + ['\'' + str(new_TP.engID) + '\''];
    if do_newnew:
        eng_IDs_list = eng_IDs_list + ['\'' + str(newnew_TP.engID) + '\''];
        
    # Format our lists of data for sql pull.
    format_operations = (','.join(map(str, operation_list))) ## format operations list
    format_eng_IDs = (','.join(map(str, eng_IDs_list))) ## format Eng ID list

    with open(sql_orig, 'r') as file : # Read in the default sql script
      uber_script = file.read()
      
    # edit SQL
    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the operations
    uber_script = uber_script.replace('##OPERATIONS##',format_operations )# Replace the eng_id_list

    with open(sql_new, 'w') as file: # Write the file out again
      file.write(uber_script)

    ## run sql script
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site)); ## Selecting correct site
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(hvqk_raw_sql);
    print("HVQK Verbose sql pull created");


    return()
