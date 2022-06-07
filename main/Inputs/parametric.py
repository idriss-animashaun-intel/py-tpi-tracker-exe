import sys
import xml.etree.ElementTree
import os
import csv
import subprocess
from os.path import expanduser
import re
from .resource_path import resource_path  # allows you to use relative pathing from the current file

# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
#     base_path = re.sub(r"Inputs+$","",base_path,flags=re.I); #RC replaced split with regex to remove Inputs folder from folder path (avoid losing the I on I drive.)
#     return os.path.join(base_path, relative_path)

sch = resource_path("..\\Schedule")

# header_path = os.getcwd();
# gen_path = header_path + "\\generated_files\\jmp_para_tmp.jsl";

# print('test', gen_path)

try:
    from Inputs import PiUber
except:
    from TPITracker.Inputs import PiUber

python_exe = sys.executable
#if sys.version_info >= (3,0,0):
import pandas as pd
import numpy as np


def __init__():
    letsgo=1;

def parametric(site,schema,old_TP,new_TP,newnew_TP,do_newnew):
    # Runs the jmp script to calculate the parametric data based on the user input file.
    # 1. Pulls parametric data.
    # 2. Creates & runs jsl script to output data.
    
    print("Writing parametric SQL pull");

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
    jmp_script = header_path+"\\generated_files\\jmp_para_tmp.jsl";
    
    raw_parametric_path = header_path+"\\generated_files\\parametric_data.csv";
    
    paramList = inputParser(user_input_path);

    parametric_pull(site,schema,old_TP,new_TP,newnew_TP,paramList,raw_parametric_path,do_newnew);
    
    '''
        attempt to filter zero cols in testing 
    '''
    paramList = checkZeroCols(raw_parametric_path,paramList)
    paramList = pullChecker(raw_parametric_path,paramList);

    jmp_file_creation(paramList,jmp_script,raw_parametric_path,header_path,old_TP,new_TP,newnew_TP,do_newnew);
    print("Doing JMP");
    check_source = os.path.splitdrive(home);
    if(check_source[0] == r"C:"):
        print("Running jmp from local computer");
        subprocess.call(resource_path("..\\JMPbackgroundcaller.exe") + " generated_files\\jmp_para_tmp.jsl",shell = False);
    else:
        print("Running jmp from scripthost");
        subprocess.call(r"\\SHUser-prod.intel.com\SHprodUser$\eoghanoc\eoghanoc_scripthost\TPI_Tracker\Inputs\para_jmp.exe");
    print("JMP Parametric complete");

def parametric_pull(site,schema,old_TP,new_TP,newnew_TP,paramList,output_path,do_newnew):
    header_path = os.getcwd();
    sql_input_path = resource_path("sql_files\\parametricPull.txt");
    sql_output_path = header_path+"\\generated_files\\pull_parametric_data.aws";
    # print(source_path);

    lot_op_list = [];
    eng_IDs_list = [];
    
    eng_IDs_list = eng_IDs_list + ['\'' + str(old_TP.engID) + '\''];
    eng_IDs_list = eng_IDs_list + ['\'' + str(new_TP.engID) + '\''];

    lot_op_list = lot_op_list + ['\'' + str(old_TP.engID) + "_" + str(old_TP.op) + '\''];
    lot_op_list = lot_op_list + ['\'' + str(new_TP.engID) + "_" + str(new_TP.op) + '\''];

    if do_newnew:
        eng_IDs_list = eng_IDs_list + ['\'' + str(newnew_TP.engID) + '\''];
        lot_op_list = lot_op_list + ['\'' + str(newnew_TP.engID) + "_" + str(newnew_TP.op) + '\''];

    format_eng_IDs = (','.join(map(str, eng_IDs_list))) ## format Eng ID list
    format_lot_ops = (','.join(map(str, lot_op_list))) ## format lot_op list
    
    j=0;
    format_avg_list = "";
    format_as_list = "";
    format_case_list = "";
    format_param_list = "";
    #filter_999_block = "";
    
    for param in paramList:
        aka = param.replace("::","_");
        tmp = "\n\t,Avg({0}) AS {0}".format(aka);
        format_avg_list = format_avg_list+tmp;
            
        tmp = "\n\t\t,{0} AS {0}".format(aka);
        format_as_list = format_as_list+tmp;

        tmp = "\n\t\t\t,CASE WHEN t0.test_name = '{0}' THEN pr.numeric_result ELSE NULL END AS {1}".format(param,aka);
        format_case_list = format_case_list+tmp;

        if (j == 0):
            tmp = r"'{0}'".format(param);
            j = 1;
        else:
            tmp = "\n\t\t\t,'{0}'".format(param);
        format_param_list = format_param_list + tmp;
        #filter_999_block = filter_999_block + "\n\tAND {0} > -999".format(aka);
    
    with open(sql_input_path, 'r') as file : # Read in the default sql script
        uber_script = file.read()

    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the eng_id_list
    uber_script = uber_script.replace('##LOT_OP##',format_lot_ops)# Replace the lot_op list
    uber_script = uber_script.replace('##AVG_LIST##',format_avg_list)# Replace the lot_op list
    uber_script = uber_script.replace('##AS_LIST##',format_as_list)# Replace the lot_op list
    uber_script = uber_script.replace('##CASE_LIST##',format_case_list)# Replace the lot_op list
    uber_script = uber_script.replace('##PARAM_LIST##',format_param_list)# Replace the lot_op list
    
    with open(sql_output_path, 'w') as file: # Write the file out again
        file.write(uber_script);
    
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site));
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(output_path);
    print("Parametric sql pull created");

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
        data.to_csv(output_path,index=None)
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

def jmp_file_creation(paramList,jmp_script,raw_parametric_path,header_path,old_TP,new_TP,newnew_TP,do_newnew):
    jmp_O2N_distrib = header_path+"\\Parametric_Outputs\\O2N_distributions.jmp";
    jmp_jrnl = header_path+"\\Parametric_Outputs\\parametrics_journal.jrn";
    jmp_input = resource_path("jmp_scripts\\parametricJmp.jsl");
    jmp_O2N_r2_table = header_path+"\\Parametric_Outputs\\O2N_table_r2.jmp";
    jmp_O2N_r2 = header_path+"\\Parametric_Outputs\\O2N_r2.jrn";
    jmp_N2N_r2_table = header_path+"\\Parametric_Outputs\\N2N_table_r2.jmp";
    jmp_N2N_r2 = header_path+"\\Parametric_Outputs\\N2N_r2.jrn";
    
    var_string = "";
    col_list = "";
    j = 0;

    bivariate_save_loc = [];
    table_save_loc = [];
    lot_op_list = [];
    
    bivariate_save_loc = bivariate_save_loc + ["Insert Into(bivariate_save_loc,\""+jmp_O2N_r2+"\");\n"];
    table_save_loc = table_save_loc + ["Insert Into(table_save_loc,\""+jmp_O2N_r2_table+"\");\n"];
    lot_op_list = lot_op_list + ['\"' + str(old_TP.engID) + "_" + str(old_TP.op) + '\"'];
    lot_op_list = lot_op_list + ['\"' + str(new_TP.engID) + "_" + str(new_TP.op) + '\"'];

    if do_newnew:
        bivariate_save_loc = bivariate_save_loc + ["Insert Into(bivariate_save_loc,\""+jmp_N2N_r2+"\");\n"];
        table_save_loc = table_save_loc + ["Insert Into(table_save_loc,\""+jmp_N2N_r2_table+"\");\n"];
        lot_op_list = lot_op_list + ['\"' + str(newnew_TP.engID) + "_" + str(newnew_TP.op) + '\"'];
    
    format_biv = ('\n'.join(map(str, bivariate_save_loc))) ## format BIV list
    format_table = ('\n'.join(map(str, table_save_loc))) ## format TABLE list
    format_lot_ops = (','.join(map(str, lot_op_list))) ## format Lot OP list

    for param in paramList:
        paramQuote = "\"{0}\"".format(param); 
        if j == 0: # First line will look slightly different
            param_string = paramQuote;
            col_list = "\n\t\t\t:"+param;
            j = 1;# Just in case the first line is commented. Unusual but could happen!
        else:
            param_string = ",\n".join([param_string,paramQuote]);
            col_list = ",\n\t\t\t:".join([col_list,param]);

    with open(jmp_input, 'r') as file : # Read in the default sql script
        jmp_output = file.read()
        
    jmp_output = jmp_output.replace('##RAW_PARAM##', raw_parametric_path)# Replace the raw parametric data location
    jmp_output = jmp_output.replace('##PARAM_LIST##',param_string)# Replace the param list
    jmp_output = jmp_output.replace('##LOT_OP_LIST##',format_lot_ops)# Replace the lot_op list
    jmp_output = jmp_output.replace('##O2N_DISTRIB##',jmp_O2N_distrib)# Replace the O2N distrib save location
    jmp_output = jmp_output.replace('##JMP_JRNL##',jmp_jrnl)# Replace the jmp journal save location
    jmp_output = jmp_output.replace('##BIVARIATE_SAVE##',format_biv)# Replace the lot_op list
    jmp_output = jmp_output.replace('##TABLE_SAVE##',format_table)# Replace the lot_op list
    jmp_output = jmp_output.replace('##COLUMN_LIST##',col_list)# Replace the lot_op list
    
    with open(jmp_script, 'w') as file: # Write the file out again
        file.write(jmp_output);
    
    print("Parametric JMP script created");
