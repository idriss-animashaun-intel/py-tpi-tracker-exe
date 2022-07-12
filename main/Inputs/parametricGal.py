import sys
# import xml.etree.ElementTree
import os
import csv
import subprocess
from os.path import expanduser
try:
    from Inputs import PiUber
except:
    from TPITracker.Inputs import PiUber
import re
from .resource_path import resource_path  # allows you to use relative pathing from the current file

# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
#     base_path = re.sub(r"Inputs+$","",base_path,flags=re.I); #RC replaced split with regex to remove Inputs folder from folder path (avoid losing the I on I drive.)
#     return os.path.join(base_path, relative_path)

sch = resource_path("..\\Schedule")

python_exe = sys.executable
#if sys.version_info >= (3,0,0):

import pandas as pd
import numpy as np




def __init__():
    letsgo=1;

def parametricGal(site,schema,old_TP,new_TP,newnew_TP,do_newnew):
    # Runs the jmp script to calculate the parametric data Gal wants
    # 1. Creates & runs jsl script to output data.
    home = expanduser("~");
    header_path = os.getcwd();
    
    if (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\11\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\11\\jmp.exe";
    elif (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\12\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\12\\jmp.exe";
    elif (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\13\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\13\\jmp.exe";
    elif (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\14\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\14\\jmp.exe";
        print("I have not fully validated JMP 14, so if it breaks... I blame them and them alone.");
    elif (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\15\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\15\\jmp.exe";
        print("I have not fully validated JMP 15, so if it breaks... I blame them and them alone.");
    else:
        print("You don't have JMP 11-13, you're pretty screwed :( ");
    user_input_path =  sch + "\\{0}_Parametrics.txt".format(new_TP.name);
    jmp_script_O2N = header_path+"\\generated_files\\jmp_para_gal_O2N_tmp.jsl";
    jmp_script_N2N = header_path+"\\generated_files\\jmp_para_gal_N2N_tmp.jsl";
    
    raw_parametric_path = header_path+"\\generated_files\\parametric_data.csv";
    
    paramList = inputParser(user_input_path);
    '''
        attempt to filter zero cols in testing 
    '''
    paramList = checkZeroCols(raw_parametric_path,paramList)
    paramList = pullChecker(raw_parametric_path,paramList);
    
    jmp_file_creation(paramList,jmp_script_O2N,raw_parametric_path,header_path,old_TP,new_TP,0);
    if (do_newnew):
        jmp_file_creation(paramList,jmp_script_N2N,raw_parametric_path,header_path,new_TP,newnew_TP,1);

    print("Doing JMP using Gal's beautiful script");
    check_source = os.path.splitdrive(home);
    if(check_source[0] == r"C:"):
        print("Running jmp from local computer");
        subprocess.call(resource_path("..\\JMPbackgroundcaller.exe") + " generated_files\\jmp_para_gal_O2N_tmp.jsl",shell = False);
        if (do_newnew):
            subprocess.call(resource_path("..\\JMPbackgroundcaller.exe") + " generated_files\\jmp_para_gal_N2N_tmp.jsl",shell = False);
    print("JMP Parametric 2 complete");

def checkZeroCols(output_path,paramList):
    data = pd.read_csv(output_path,header='infer')
    updatedParametricList = []
    for i,col in enumerate(data.columns):
        if data[col].values.dtype == np.float_:
            if np.isnan(data[col].values).all():
                #print(np.isnan(data[col].values).all(),col,i)
                data = data.drop([col],axis=1)
            else:
                updatedParametricList.append(col)
    if updatedParametricList == paramList:
        return paramList
    else:
        #probs not needed come back to this as its already been updated in other parametric
        #data.to_csv(output_path,index=None)
        return updatedParametricList

def inputParser(user_input_path):
    # Parses the input file into a known list
    paramList = [];
    
    for line in open(user_input_path):
        val = line.strip();
        if val.startswith("\""):
            val = val.replace("\"","");
        paramList.append(val);

    return paramList;

def pullChecker(raw_parametric_path,paramList):
    # This function will check that there is data available for all requested data. This is to prevent missing rows killing us...
    finalParamList = [];
    with open(raw_parametric_path, newline='') as f:
        reader = csv.reader(f)
        sqlResultList = next(reader)  # gets the first line

    for param in paramList:
        param = param.replace("::","_");
        if param in sqlResultList:
            finalParamList.append(param);
        else:
            print("Param {0} could not be found in either old or new TP... plz investigate".format(param));

    return finalParamList;

def jmp_file_creation(paramList,jmp_script,raw_parametric_path,header_path,old_TP,new_TP,is_newnew):
    jmp_input = resource_path("jmp_scripts\\parametricJmpGal.jsl");
    saveLoc = "";
    var_string = "";
    col_list = "";
    param_string = "";
    param_string_old = "";
    param_string_new = "";
    j = 0;

    lot_op_list = [];
    lot_op_list = lot_op_list + ['\"' + str(old_TP.engID) + "_" + str(old_TP.op) + '\"'];
    lot_op_list = lot_op_list + ['\"' + str(new_TP.engID) + "_" + str(new_TP.op) + '\"'];

    if is_newnew:
        saveLoc = header_path+"\\Parametric_Outputs\\N2N";
    else:
        saveLoc = header_path+"\\Parametric_Outputs\\O2N";
    format_lot_ops = (','.join(map(str, lot_op_list))) ## format Lot OP list

    for param in paramList:
        paramQuote = "\"{0}\"".format(param); 
        if j == 0: # First line will look slightly different
            param_string = paramQuote;
            param_string_old = "\"{0} {1}_{2}\"".format(param,old_TP.engID,old_TP.op); 
            param_string_new = "\"{0} {1}_{2}\"".format(param,new_TP.engID,new_TP.op); 
            j = 1;# Just in case the first line is commented. Unusual but could happen!
        else:
            param_string = ",\n\t".join([param_string,paramQuote]);
            param_string_old = ",\n\t".join([param_string_old,("\"{0} {1}_{2}\"".format(param,old_TP.engID,old_TP.op))]);
            param_string_new = ",\n\t".join([param_string_new,("\"{0} {1}_{2}\"".format(param,new_TP.engID,new_TP.op))]);

    with open(jmp_input, 'r') as file : # Read in the default sql script
        jmp_output = file.read()
        
    jmp_output = jmp_output.replace('##SAVE_LOC##', saveLoc)# Replace the raw parametric data location
    jmp_output = jmp_output.replace('##RAW_PARAM##', raw_parametric_path)# Replace the raw parametric data location
    jmp_output = jmp_output.replace('##LOT_OP_LIST##',format_lot_ops)# Replace the lot_op list
    jmp_output = jmp_output.replace('##PARAM_LIST##',param_string)# Replace the param list
    jmp_output = jmp_output.replace('##PARAM_LIST_OLD##',param_string_old)# Replace the O2N distrib save location
    jmp_output = jmp_output.replace('##PARAM_LIST_NEW##',param_string_new)# Replace the jmp journal save location
    
    with open(jmp_script, 'w') as file: # Write the file out again
        file.write(jmp_output);
    
    print("Parametric JMP script created");
