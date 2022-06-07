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

sch = resource_path("..\\Schedule")

def vadtl_csv_creator(old_TP,new_TP,newnew_TP,site,wfr_coord, do_newnew):
    # This function pulls together all our vadtl info
    home = expanduser("~");
    header_path = os.getcwd();
    
    vadtl_xml_loc =  sch + "\\{0}_vadtl.xml".format(new_TP.name);
    sql_orig = resource_path("sql_files\\Vadtl_pull.txt");
    sql_new = header_path+"\\generated_files\\Vadtl_pull.txt";
    vadtl_raw_sql = header_path+"\\generated_files\\Vadtl_raw_pull.csv";

    [sql_list,mbit_thresholds] = vadtl_xml_parser(vadtl_xml_loc);

    VADTL_sql_pull(sql_list,old_TP,new_TP,newnew_TP,sql_orig,sql_new,vadtl_raw_sql,site,wfr_coord, do_newnew,mbit_thresholds);


## Filter xml for threshold and token names
def vadtl_xml_parser(vadtl_xml_loc):

    ##Open xml for parsing
    tree = ET.parse(vadtl_xml_loc) ## open xml in xml parser
    root = tree.getroot()

    ## Initilise varibles to store thrshold and token lists
    sql_list = [] ## store sql tokens to pull
    thresholds = [] ## store threshold values
    mbit_thresholds = dict()
    ##Get mbit_mane
    for child in root:
        mbit_name = (child.attrib["name"])
        break

    for domain in root.findall("./domain"):
        threshold = float(domain.attrib["threshold"])
        if (domain.attrib["datalog_mode"] == "EXTENDED"):
            domain_name = "HVQK_SHIFT_"+domain.attrib["name"]
            #sql_list.append('\'' + domain_name + '\'') ## populate list for sql search
            for shift in domain.findall("./shift"):
                shift_name = "HVQK_VMIN_SHIFT_"+shift.attrib["name"]
                sql_list.append('\'' + shift_name + '\'') ## populate list for sql search
                mbit_thresholds[shift_name] = domain_name + ":" + domain.attrib["threshold"]
        else:
            shift_name = mbit_name+"_"+domain.attrib["name"]
            sql_list.append('\'' + mbit_name+"_"+domain.attrib["name"] + '\'') ## populate list for sql search
            thresholds.append(threshold) ## get vadtl threshold values
            mbit_thresholds[shift_name] = shift_name + ":" + domain.attrib["threshold"]

    return(sql_list,mbit_thresholds)



def VADTL_sql_pull(sql_list,old_TP,new_TP,newnew_TP,sql_orig,sql_new,vadtl_raw_sql,site,wfr_coord, do_newnew,mbit_thresholds):    
    # This script does the thing

    operation_list = [];
    eng_IDs_list = [];
    vadtl_check=""
    
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
    format_tokens = (','.join(map(str, sql_list))) ## format token list
    format_operations = (','.join(map(str, operation_list))) ## format operations list
    format_eng_IDs = (','.join(map(str, eng_IDs_list))) ## format Eng ID list

    with open(sql_orig, 'r') as file : # Read in the default sql script
      uber_script = file.read()

    #Create CASE statement for Vmin Shift vs Threshold
    shift_count=0
    for shift in mbit_thresholds:
        split = mbit_thresholds[shift].split(":")
        mbit_domain = split[0]
        threshold = split[1]
        if shift_count == 0:
            vadtl_check+=str(",CASE WHEN test_name = \'" + shift + "\' THEN CASE WHEN numeric_result > " + threshold + " THEN \'" +  mbit_thresholds[shift] + "\' else '0' END ")
        else:
            vadtl_check+=str("WHEN test_name = \'" + shift + "\' THEN CASE WHEN numeric_result > " + threshold + " THEN \'" +  mbit_thresholds[shift] +"\' else '0' END ")
        shift_count+=1
    vadtl_check+=str("else 'VMIN Shift name not found' END AS vadtl_status")

    # edit SQL
    uber_script = uber_script.replace('##TOKEN_LIST##', format_tokens)# Replace the token list
    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the operations
    uber_script = uber_script.replace('##OPERATIONS##',format_operations )# Replace the eng_id_list
    uber_script = uber_script.replace('##WFR_COORD##',wfr_coord )# Replace the WFR_COORD to pull historical data
    uber_script = uber_script.replace('##VADTL_CHECK##',vadtl_check )# Replace the VADTL_CHECK to check Vmin shift against Theshold voltage

    with open(sql_new, 'w') as file: # Write the file out again
      file.write(uber_script)

    ## run sql script
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site)); ## Selecting correct site
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(vadtl_raw_sql);
    print("Vadtl sql pull created");


    return()
