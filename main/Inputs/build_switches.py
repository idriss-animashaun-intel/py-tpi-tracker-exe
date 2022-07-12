import sys
import xml.etree.ElementTree
import os
import csv
import subprocess
from os.path import expanduser
import itertools
import operator
import numpy

def __init__():
    letsgo=1;

def build_switches(comp_type,do_newnew):
# This script takes the raw data generated (and neatly organised from the jmp script), and 
# uses it to determine what die have switched from old to new [either fbin or ibin depending
# on the input variable comp_type]
    print("Generating Bin switches list");
    header_path = os.getcwd();
    script_input_path = header_path+"\\Outputs\\{{csv}}0_RawData_Matching_WFRS_FINAL.csv";
    output_dir = header_path+"\\Outputs\\switches_auto.csv";
    # print(output_dir);
    switch_dir = header_path+"\\Outputs\\switches.csv";
    items = [];
    j = [];
    
    for i,line in enumerate(open(script_input_path)):
        if (i == 0):
            header = line.strip().split(",");
        else:
            if do_newnew:
                items.append(line.strip().split(","));
            else:
                temp_line = line.strip().split(",");
                t = ["0"]
                merged_line = temp_line[0:7] + t+ temp_line[7:9] + t + temp_line[9:11] + t;
                items.append(merged_line);
            
    no_die_tested_total = len(items);
    # print(no_die_tested_total);
        
    if sys.version_info >= (3,0,0):
        output_csv = open(output_dir, 'w',newline = ''); 
    else:
        output_csv = open(output_dir, 'wb');
    writer = csv.writer(output_csv);

    writer.writerow(["Wafer_id","sort_x","sort_y","Tray_Loc","OLD_IB","N_IB","NN_IB","OLD_FB","N_FB","NN_FB","O2N_IBSwitch","N2N_IBSWITCH","O2N_Switch","N2N_SWITCH","Module","Owner","O_Site","N_Site","NN_Site"]);
    
    for i in range(0,no_die_tested_total):
        do_print = 1;

        ib_o = items[i][5];
        ib_n = items[i][6];
        ib_nn = items[i][7];
        fb_o = items[i][8];
        fb_n = items[i][9];
        fb_nn = items[i][10];
        for j in range(0,3):
            # Try block for CMT/other bug. Basically the cell info isn't vital, so if it isn't 
            # printing we'll just leave it as N/A and push on with the important stuff
            try:
                if (items[i][11+j][0] == "1"):
                    items[i][11+j] = "A"+items[i][11+j][1:4];
                elif (items[i][11+j][0] == "2"):
                    items[i][11+j] = "B"+items[i][11+j][1:4];
                elif (items[i][11+j][0] == "3"):
                    items[i][11+j] = "C"+items[i][11+j][1:4];
                elif (items[i][11+j][0] == "4"):
                    items[i][11+j] = "D"+items[i][11+j][1:4];
                elif (items[i][11+j][0] == "5"):
                    items[i][11+j] = "E"+items[i][11+j][1:4];
                else:
                    items[i][11+j] = "N/A";
            except:
                items[i][11+j] = "N/A";
        
        # 0:4 gives up to tray ID, 4 gives no_rows (a useless param) so we skip it. 5-11 is bins
        outputrow_1 = items[i][0:4];
        outputrow_2 = items[i][5:11];
        outputrow_3 = [];
        outputrow_4 = [];
        
        # Old to new switch printing
        if ((comp_type == "fbin") and (fb_o != fb_n)):
            outputrow_3 = [str(fb_o+(">")+(str(fb_n)))];
            outputrow_4 = [str(fb_o+(">")+(str(fb_n)))];
        elif ((comp_type == "ibin") and (ib_o != ib_n)):
            outputrow_3 = [str(ib_o+(">")+(str(ib_n)))];
            outputrow_4 = [str(ib_o+(">")+(str(ib_n)))];
        else:
            outputrow_3 = ["0"];
            outputrow_4 = ["0"];

        # New to NewNew switch printing (only do newnew check if newnew is enabled)
        if ((comp_type == "fbin") and (fb_n != fb_nn) and do_newnew):
            outputrow_3 = outputrow_3+[str(fb_n+(">")+(str(fb_nn)))];
            outputrow_4 = outputrow_4+[str(fb_n+(">")+(str(fb_nn)))];
        elif ((comp_type == "ibin") and (ib_n != ib_nn) and do_newnew):
            outputrow_3 = outputrow_3+[str(ib_n+(">")+(str(ib_nn)))];
            outputrow_4 = outputrow_4+[str(ib_n+(">")+(str(ib_nn)))];
        else:
            outputrow_3 = outputrow_3+["0"];
            outputrow_4 = outputrow_4+["0"];
                
        # Print row if switch occurs (only do newnew check if newnew is enabled)
        if do_newnew:
            if (fb_n == fb_o and fb_n == fb_nn and comp_type == "fbin"):
                do_print = 0;
            elif (ib_n == ib_o and ib_n == ib_nn and comp_type == "ibin"):
                do_print = 0;
        else:
            if (fb_n == fb_o and comp_type == "fbin"):
                do_print = 0;
            elif (ib_n == ib_o and comp_type == "ibin"):
                do_print = 0;
                
        outputrow_5 = ["0","0",items[i][11],items[i][12],items[i][13]];
            
                
        if (do_print):
            outputrow = outputrow_1+outputrow_2+outputrow_3+outputrow_4+outputrow_5;
            # print(outputrow);
            writer.writerow(outputrow);
        # if (i[10])
        
    # print(j[0][0]);
    output_csv.close();
    print("Bin switches list generation Complete");
    # no_die = j[8];
    # print(items[0]);
    