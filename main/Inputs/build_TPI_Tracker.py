import sys
import xml.etree.ElementTree
import os
import csv
import subprocess
import glob
from os.path import expanduser
import itertools
import operator
import re
from .resource_path import resource_path

# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
#     base_path = re.sub(r"Inputs+$","",base_path,flags=re.I); #RC replaced split with regex to remove Inputs folder from folder path (avoid losing the I on I drive.)
#     return os.path.join(base_path, relative_path)

source_path = os.getcwd();
# sys.path.insert(0, resource_path('Inputs\\XlsxWriter\\'));

python_exe = sys.executable
try:
    import numpy as np
except:
    print("need to import numpy using pip");
    subprocess.call(python_exe + ' -m pip install --upgrade pip --proxy="http://proxy-chain.intel.com:911"')
    subprocess.call(python_exe + ' -m pip install numpy --proxy="http://proxy-chain.intel.com:911"');
    import numpy as np

if sys.version_info <= (3,0,0):
    from io import open

def __init__():
    letsgo=1;

def build_dff(workbook, output_dir, tp_short):
     # print(output_dir);
    if sys.version_info >= (3,0,0):
        output_csv = open(output_dir, 'w',newline = '');
    else:
        output_csv = open(output_dir, 'wb');
    writer = csv.writer(output_csv);
    writer.writerow(["DFF","HitRate","Desicion","Explanation"]);
    writer.writerow(["a","0","a","c"]);
    writer.writerow(["b","1","a","d"]);
    output_csv.close();

    norm = workbook.add_format({
    'border': 1});

    green_bold = workbook.add_format({
    'bold': 1,
    'border': 1,
    'bg_color':'green'});

    yellow_bold = workbook.add_format({
    'bold': 1,
    'border': 1,
    'bg_color':'yellow'});

    dff_sheet = workbook.add_worksheet("DFF_"+tp_short);
    with open(output_dir, 'rt', encoding='utf8') as f:
        reader = csv.reader(f);
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                if (r == 0):
                    dff_sheet.write(r, c, col,green_bold);
                else:
                    if (c==1 and float(row[1])<0.9):
                        dff_sheet.write(r, c, col,yellow_bold);
                    else:
                        dff_sheet.write(r, c, col);
    dff_sheet.hide();
    return workbook

def build_hvqk_verbose(workbook, output_dir):
    hvqk_verbose_sheet = workbook.add_worksheet("HVQK_VERBOSE");
    with open(output_dir, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                hvqk_verbose_sheet.write(r, c, col);
    hvqk_verbose_sheet.hide();
    return workbook

def build_dispo(workbook, name,old_TP,new_TP,newnew_TP,lazy_var):
    switch_sheet = workbook.add_worksheet(name);
    o_shrt = old_TP.name[10:15];
    n_shrt = new_TP.name[10:15];

    # Column width setup
    cols =   ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O"];
    widths = [13, 13, 11.5,10.5,10.5,10.5,13, 13, 40, 40, 20, 20,  21,20, 20];
    for i in range(0,len(cols)):
        switch_sheet.set_column(cols[i]+':'+cols[i], widths[i]);
    switch_sheet.set_row(3, 45);
    # FORMAT SETUPS
    blue_norm = workbook.add_format({
    'text_wrap':'1',
    'bg_color':'#CCECFF'});

    merge_green = workbook.add_format({
    'bold': 1,
    'align': 'center',
    'valign': 'vcenter',
    'bg_color':'#CCFFCC'})

    merge_purple = workbook.add_format({
    'bold': 1,
    'align': 'center',
    'valign': 'vcenter',
    'bg_color':'#CCCCFF'})

    merge_blue = workbook.add_format({
    'bold': 1,
    'align': 'center',
    'valign': 'vcenter',
    'bg_color':'#CCECFF'})

    # CELL FILLS
    # switch_sheet.write(blue_norm);

    lot_line = "New Lot: "+new_TP.engID+"/"+newnew_TP.engID+" Old Lot: "+old_TP.engID;
    switch_sheet.merge_range('A1:O1', new_TP.name, merge_green);
    switch_sheet.merge_range('A2:O2', lot_line, merge_purple);
    switch_sheet.merge_range('A3:O3', 'COMMS', merge_blue);

    cols = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O"];
    comms1=["Old Owner","New Owner","Wafer","Sort_X","Sort_Y","Tray_Loc"];
    comms2=["O2N:\n"+old_TP.engID+"->\n"+new_TP.engID,"N2N:\n"+new_TP.engID+"->\n"+newnew_TP.engID];
    comms3=["O2N COMMS","N2N COMMS","O2N switches","N2N switches"];
    comms4=["Was a Shmoo\ncompleted (yes/no)","Old Failing Module","New Failing Module"];
    comms = comms1+comms2+comms3+comms4;
    for i in range(0,len(comms)):
        spot = cols[i]+"4";
        switch_sheet.write(spot,comms[i],blue_norm);

    dispo_cols = ["A","B","C","D","E","F","N","O"];
    raw_cols =   ["P","R","A","B","C","D","O","Q"];
    for i in range(0,len(dispo_cols)):
        for j in range(0,lazy_var):#
            exact_dispo = dispo_cols[i]+str(j+5);
            exact_raw = raw_cols[i]+str(j+2);
            switch_sheet.write(exact_dispo,'=Raw_Data!'+exact_raw);

    dispo_cols = ["G","H"];
    comp_cols = ["A","B"];
    raw_cols =   ["M","N"];
    for i in range(0,len(dispo_cols)):
        for j in range(0,lazy_var):#
            exact_dispo = dispo_cols[i]+str(j+5);
            exact_comp = comp_cols[i]+str(j+5);
            exact_raw = raw_cols[i]+str(j+2);
            var1 = "=IF(";
            var2 = exact_comp;
            var3 = """="0","",Raw_Data!""";
            var4 = exact_raw;
            var5 = ")";
            data = var1+var2+var3+var4+var5;
            switch_sheet.write(exact_dispo,data);

    for i in range(0,lazy_var):#
        a_check = "A"+str(i+5);
        h_check = "I"+str(i+5);
        j_check = "K"+str(i+5);
        O2Nif1 = "=IF(("+a_check;
        O2Nif2 = """="0"),"N/A",(IF(("""+h_check;
        O2Nif3 = """<>""),"Complete","""+a_check+")))";
        O2Nif = O2Nif1+O2Nif2+O2Nif3;
        switch_sheet.write(j_check,O2Nif);

    for i in range(0,lazy_var):#
        b_check = "B"+str(i+5);
        i_check = "J"+str(i+5);
        k_check = "L"+str(i+5);
        O2Nif1 = "=IF(("+b_check;
        O2Nif2 = """="0"),"N/A",(IF(("""+i_check;
        O2Nif3 = """<>""),"Complete","""+b_check+")))";
        O2Nif = O2Nif1+O2Nif2+O2Nif3;
        switch_sheet.write(k_check,O2Nif);

    return workbook

def build_main(workbook, main_name,old_TP,new_TP,newnew_TP,flow):

    header_path = os.getcwd();
    vmu_vb = [];
    vmu_pb = [];
    with open(header_path + '/generated_files/pull_vmu_data.csv') as vmufile:
        vmureader = csv.reader(vmufile)
        next(vmureader)
        for row in vmureader:
            if row == '':
                break
            test_name = row[12];
            test_val = int(row[13]);
                
            if "VB" in test_name:
                vmu_vb.append(test_val);
            elif "PB" in test_name:
                vmu_pb.append(test_val);
            else:
                print("what are you even findings?");
    
    vmu_vb_mean = np.mean(vmu_vb);
    vmu_vb_max = max(vmu_vb);
    vmu_pb_mean = np.mean(vmu_pb);
    vmu_pb_max = max(vmu_pb);

    vmu_vb_mean = str(int(vmu_vb_mean/(1024*1024)));
    vmu_vb_max = str(int(vmu_vb_max/(1024*1024)));
    vmu_pb_mean = str(int(vmu_pb_mean/(1024*1024)));
    vmu_pb_max = str(int(vmu_pb_max/(1024*1024)));
    
    main_sheet = workbook.add_worksheet(main_name);
    o_shrt = old_TP.name[10:15];
    n_shrt = new_TP.name[10:15];

    # Column width setup
    main_sheet.set_column('B:C', 25);
    main_sheet.set_column('F:F', 25);
    main_sheet.set_column('D:E', 9.5);

    # FORMAT SETUPS
    blue_norm = workbook.add_format();
    blue_norm.set_pattern(1);
    blue_norm.set_bg_color('#CCECFF');

    blue_bold = workbook.add_format();
    blue_bold.set_pattern(1);
    blue_bold.set_bold();
    blue_bold.set_bg_color('#CCECFF');

    blue_bold_bord = workbook.add_format();
    blue_bold_bord.set_pattern(1);
    blue_bold_bord.set_bold();
    blue_bold_bord.set_bg_color('#CCECFF');
    blue_bold_bord.set_border(1);

    red_norm = workbook.add_format();
    red_norm.set_pattern(1);
    red_norm.set_bg_color('red');

    merge_bold = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter'})

    merge_blue = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter'});
    merge_blue.set_bg_color('#CCECFF');

    all_bord = workbook.add_format({
    'border':1});

    # BORDERS
    row1 = [12,12,56,56,74];
    row2 = [53,53,85,73,85];
    col1 = [1,10,1,8,8];
    col2 = [9,24,8,24,24];
    added_rule = {'bg_color':'#CCECFF'};
    for i in range(0,len(row1)):
        box(workbook,main_sheet,row1[i],col1[i],row2[i],col2[i], added_rule);

    row1 = [1,3,8];
    row2 = [2,5,9];
    col1 = [1,1,1];
    col2 = [3,1,1];
    added_rule = {};
    for i in range(0,len(row1)):
        box(workbook,main_sheet,row1[i],col1[i],row2[i],col2[i], added_rule);
    # CELL FILLS
    main_sheet.write('B2', 'TP Name', blue_bold_bord);
    main_sheet.write('B3', '', blue_bold_bord);
    main_sheet.write('C3', 'TP Name', blue_bold_bord);
    main_sheet.write('D3', 'Eng_ID', blue_bold_bord);
    main_sheet.write('E3', 'Operation', blue_bold_bord);
    main_sheet.write('B9', 'Confirm Spoofi has been checked', blue_bold_bord);
    main_sheet.write('B10', 'Confirm Raster has been checked', blue_bold_bord);
    main_sheet.write('C9', '', red_norm);
    main_sheet.write('C10', '', red_norm);
    
    main_sheet.write('P2', 'Physical Memory [Mean]')
    main_sheet.write('P3', vmu_pb_mean + 'MB')
    main_sheet.write('Q2', 'Virtual Memory [Mean]')
    main_sheet.write('Q3', vmu_vb_mean + 'MB')
    main_sheet.write('R2', 'Physical Memory [Max]')
    main_sheet.write('R3', vmu_pb_max + 'MB')
    main_sheet.write('S2', 'Virtual Memory [Max]')
    main_sheet.write('S3', vmu_vb_max + 'MB')

    main_sheet.merge_range('H2:N2', 'KAPPA REPORT', merge_bold);
    main_sheet.merge_range('H3:N6', '', merge_blue);

    main_sheet.merge_range('B12:J12', 'TRC LINK REQUIRED', merge_blue);
    main_sheet.merge_range('B11:J11', 'OLD > NEW', merge_bold);
    main_sheet.merge_range('K12:Y12', 'TRC LINK REQUIRED', merge_blue);
    main_sheet.merge_range('K11:Y11', 'NEW > NEW', merge_bold);

    main_sheet.merge_range('B56:H56', 'Switches Summary', merge_bold);
    main_sheet.merge_range('I56:Y56', 'Test Time Summary', merge_bold);
    main_sheet.merge_range('I74:Y74', 'Application Rate', merge_bold);
    main_sheet.insert_image('J58','Outputs/{{PIC}}TestTime_Brief.jpg');
    comp = int(old_TP.op);
    if ((comp < 132350 or comp > 132365) and (comp != 132150)):
        main_sheet.insert_image('J76','Outputs/{{PIC}}HVQK_GD_application_Rate.jpg');

    main_sheet.write('C2', main_name, blue_bold_bord);

    temp = ['Old','New','NewNew'];
    for i in range(0,3):
        cell = 'B'+str(i+4);
        main_sheet.write(cell, temp[i], blue_bold_bord);

    temp = [o_shrt,n_shrt,n_shrt];
    for i in range(0,3):
        cell = 'C'+str(i+4);
        main_sheet.write(cell, temp[i], all_bord);

    temp = [old_TP.engID,new_TP.engID,newnew_TP.engID];
    for i in range(0,3):
        cell = 'D'+str(i+4);
        main_sheet.write(cell, temp[i], all_bord);

    temp = [old_TP.op,new_TP.op,newnew_TP.op];
    for i in range(0,3):
        cell = 'E'+str(i+4);
        main_sheet.write(cell, temp[i], all_bord);

    # output_csv.close();
    return workbook

def add_to_format(existing_format, dict_of_properties, workbook):
    """Give a format you want to extend and a dict of the properties you want to
    extend it with, and you get them returned in a single format"""
    new_dict={}
    if sys.version_info >= (3,0,0):
        for key, value in existing_format.__dict__.items():
            if (value != 0) and (value != {}) and (value != None):
                new_dict[key]=value
        del new_dict['escapes']
        return(workbook.add_format(dict(new_dict.items() | dict_of_properties.items())))
    else:
        for key, value in existing_format.__dict__.iteritems():
            if (value != 0) and (value != {}) and (value != None):
                new_dict[key]=value
        del new_dict['escapes']
        return(workbook.add_format(dict(new_dict.items() + dict_of_properties.items())))

def box(workbook, sheet_name, row_start, col_start, row_stop, col_stop, added_rule):
    """Makes an RxC box. Use integers, not the 'A1' format"""

    rows = row_stop - row_start + 1
    cols = col_stop - col_start + 1
    if sys.version_info >= (3,0,0):
        for x in range((rows) * (cols)): # Total number of cells in the rectangle
            box_form = workbook.add_format(added_rule)   # The format resets each loop
            row = row_start + (x // cols)
            column = col_start + (x % cols)

            if x < (cols):                     # If it's on the top row
                # box_form = add_to_format(box_form, {'top':1, 'bg_color':'#CCECFF'}, workbook)
                box_form = add_to_format(box_form, {'top':1}, workbook)
            if x >= ((rows * cols) - cols):    # If it's on the bottom row
                # box_form = add_to_format(box_form, {'bottom':1, 'bg_color':'#CCECFF'}, workbook)
                box_form = add_to_format(box_form, {'bottom':1}, workbook)
            if x % cols == 0:                  # If it's on the left column
                # box_form = add_to_format(box_form, {'left':1, 'bg_color':'#CCECFF'}, workbook)
                box_form = add_to_format(box_form, {'left':1}, workbook)
            if x % cols == (cols - 1):         # If it's on the right column
                # box_form = add_to_format(box_form, {'right':1, 'bg_color':'#CCECFF'}, workbook)
                box_form = add_to_format(box_form, {'right':1}, workbook)

            sheet_name.write(row, column, "", box_form)
    else:
        for x in xrange((rows) * (cols)): # Total number of cells in the rectangle
            box_form = workbook.add_format()   # The format resets each loop
            row = row_start + (x // cols)
            column = col_start + (x % cols)

            if x < (cols):                     # If it's on the top row
                box_form = add_to_format(box_form, {'top':1, 'bg_color':'#CCECFF'}, workbook)
            if x >= ((rows * cols) - cols):    # If it's on the bottom row
                box_form = add_to_format(box_form, {'bottom':1, 'bg_color':'#CCECFF'}, workbook)
            if x % cols == 0:                  # If it's on the left column
                box_form = add_to_format(box_form, {'left':1, 'bg_color':'#CCECFF'}, workbook)
            if x % cols == (cols - 1):         # If it's on the right column
                box_form = add_to_format(box_form, {'right':1, 'bg_color':'#CCECFF'}, workbook)

        sheet_name.write(row, column, "", box_form)

def build_raw(workbook, output_dir):
    raw_sheet = workbook.add_worksheet("Raw_Data");
    lazy_var = 0;
        
    #if sys.version_info >= (3,0,0):
    with open(output_dir, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                raw_sheet.write(r, c, col)
    #else:
    #    output_csv = open(output_dir, 'wb');
   
    lazy_var = r;
    raw_sheet.hide();
    return workbook, lazy_var

def build_historic(workbook, output_dir):
    historic_sheet = workbook.add_worksheet("Historic_Data_for_switching_die");
    with open(output_dir, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                historic_sheet.write(r, c, col);
    return workbook

def build_vadtl(workbook, output_dir):
    vadtl_sheet = workbook.add_worksheet("VADTL_raw_data");
    with open(output_dir, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                vadtl_sheet .write(r, c, col);
    return workbook

def build_slice(workbook, output_dir):
    slice_sheet = workbook.add_worksheet("Slice_raw_data");
    with open(output_dir, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                slice_sheet .write(r, c, col);
    return workbook

def build_B99(workbook, output_dir):
    b99_sheet = workbook.add_worksheet("B99_raw_data");
    with open(output_dir, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                b99_sheet .write(r, c, col);
    return workbook

def build_TPI_Tracker(old_TP,new_TP,newnew_TP,flow,do_vadtl,do_newnew):
# Core of the script, builds out the final excel sheet to the parent directory,
# calling different functions for every excel worksheet.

    import xlsxwriter# as excel

 

    tp_short = new_TP.name[10:13];
    tp_mid = new_TP.name[10:14];
    product_name = new_TP.name[0:3];

    # source_path = os.getcwd();
    header_path = os.getcwd();
    raw_data_dir = header_path+"\\Outputs\\Switches_with_Module_Owners.csv";
    dispo_name = "Switches_"+tp_short;
    main_name = tp_mid+"_Overview";
    dff_dir = header_path+"\\Outputs\\DFF_"+tp_short+".csv";
    hist_dir = header_path+"\\generated_files\\historic_data.csv";
    vadtl_dir = header_path+"\\generated_files\\Vadtl_raw_pull.csv";
    slice_dir = header_path+"\\generated_files\\slice_raw_pull.csv";
    hvqk_verbose_dir = header_path+"\\Outputs\\hvqkVerbosePull.csv";
    B99_dir = header_path+"\\generated_files\\B99_raw_pull.csv";
    final_output_dir = header_path+"\\TPI_TRACKER_"+tp_short+".xlsl";

    workbook = xlsxwriter.Workbook(tp_short+"_"+product_name+'_TPI_TRACKER_OUTPUT.xlsx')

    workbook = build_main(workbook,main_name,old_TP,new_TP,newnew_TP,flow);
    (workbook,lazy_var) = build_raw(workbook,raw_data_dir);
    workbook = build_dispo(workbook,dispo_name,old_TP,new_TP,newnew_TP,lazy_var);
    workbook = build_dff(workbook,dff_dir,tp_short);
    workbook = build_hvqk_verbose(workbook,hvqk_verbose_dir);
    workbook = build_historic(workbook,hist_dir);
    workbook = build_B99(workbook,B99_dir);
    workbook = build_slice(workbook,slice_dir);
    if (do_vadtl):
        workbook = build_vadtl(workbook,vadtl_dir);
    # switch_sheet.activate();

    workbook.close();

    TPI_Tracker_Name = header_path+"\\"+tp_short+"_"+product_name+'_TPI_TRACKER_OUTPUT.xlsx';
    return TPI_Tracker_Name;
