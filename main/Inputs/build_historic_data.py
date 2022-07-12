import sys
import xml.etree.ElementTree
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

def build_historic_data(site, schema, output_dir, tp_name, flow):
    print("Generating IBIN History of switches");
    home = expanduser("~");
    header_path = os.getcwd();
    items = [];
    wfr_x_y = [];
    output_path = header_path+"\\generated_files\\historic_data.csv";
    
    for i,line in enumerate(open(output_dir)):  
        if (i == 0):
            header = line.strip().split(",");
        else:
            items.append(line.strip().split(","));
    
    for i in range(0,len(items)):
        if (len(items[i][0]) == 1):
            items[i][0] = "0"+items[i][0];
        if (len(items[i][0]) == 2):
            items[i][0] = "0"+items[i][0];
        wfr_x_y.append(items[i][0]+"_"+items[i][1]+"_"+items[i][2]);

    if (items[0][1] != 0 and items[0][1] != 0):
        wfr_coord = "\'" + "\'\n,\'".join(wfr_x_y)+"\'";
    
    print("Pulling SQL for historic data");
    generate_die_history_sql(site, wfr_coord, tp_name, flow, output_path);
    print("Completed historic data pull");

    return(wfr_coord)

def generate_die_history_sql(site, wfr_coord, tp_name, flow, output_path):
    print("Generating Die History SQL pull");
    header_path = os.getcwd();
    sql_input_path = resource_path("sql_files\\historyPull.txt");
    sql_output_path = header_path+"\\generated_files\\pull_die_history_data.txt";
    

    tp_13 = tp_name[0:12];
    # print(tp_13);
    # print(tp_name);
    if (flow == "SORT"):
        tp_generic = tp_13+"____";
    else:
        tp_generic = tp_13+"_______";
    
    with open(sql_input_path, 'r') as file : # Read in the default sql script
      uber_script = file.read()

    uber_script = uber_script.replace('##TP_GENERIC##', tp_generic)# Replace the operations
    uber_script = uber_script.replace('##WFR_COORD##',wfr_coord )# Replace the eng_id_list
    
    with open(sql_output_path, 'w') as file: # Write the file out again
      file.write(uber_script);
    
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site)); ## Selecting correct site
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(output_path);
    print("Die History SQL script created");
