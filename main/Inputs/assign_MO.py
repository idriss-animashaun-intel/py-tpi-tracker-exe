import sys
import xml.etree.ElementTree
import os
import csv
import re
from .resource_path import resource_path


sch = resource_path("..\\Schedule")

def __init__():
    letsgo=1;

def assign_mo(old_TP,new_TP,newnew_TP, switch_dir, output_dir,do_newnew):
# Start of script, just some basic stuff, mainly it calls the core script
    print("Assigning Bin switches to MO's");
    if sys.version_info >= (3,0,0):
        output_csv = open(output_dir, 'w',newline = '');
    else:
        output_csv = open(output_dir, 'wb');
    writer = csv.writer(output_csv);
    TPI_tracker(old_TP, new_TP, switch_dir, writer,do_newnew);
    output_csv.close();
    print("MO's assigned successfully!");
    
def get_hierarchy_list(TP):
# This script takes a look @ binner or good die config to pull the binning hierarchy. If multiple
# good die configs are present, user is prompted to select one.
    wantLine = False;

    source_path = os.getcwd();
    try:
        hierarchy = sch + "\\{0}.ub.xml".format(TP.name);

        e = xml.etree.ElementTree.parse(hierarchy).getroot();
        temp_element = e.findall('ib_hierarchy');
        temp_list = temp_element[0].text;
        hList = temp_list.split(",");
    except:
        print("gooddieconfig time");
        gdc_file = sch + "\\GoodDieConfig_{0}.txt".format(TP.name);
        for line in open(gdc_file):
            if wantLine == True:
                hList = line.strip().split(",")
                break
            items = line.split()
            if len(items) >0:
                if items[0] == "*IB_HIERARCHY*":
                    wantLine = True
                
    return [x.lstrip("0") for x in hList]
       
def get_bin_dict(TP):
# Pulls the bin report from the new TP
    source_path = os.getcwd();
    binReport = sch + "\\{0}_BinReport.xml".format(TP.name);

    e = xml.etree.ElementTree.parse(binReport).getroot();

    bins = {}
    i=0;
    for atype in e.findall('Element'):
        b = atype.find('Testname').get('name')
        a =  atype.get('name').strip("_pass")
        if (len(a) <= 3):
            bins[a] = b.split("::")[0].lstrip("0")
        else:
            bins[a[-4:]] = b.split("::")[0].lstrip("0")
    return bins

def get_MOs_dict(old_TP, new_TP):
# This script takes a look @ old & new integ reports, and uses them to determine the
# MO's of each module. The new one takes priority, but the old has to be checked in case
# of a module being removed/added between TP's. This was originally from a sighting where:
# 
# Old TP fails for module X, which is removed in new TP. 
# Old bin is higher in hierarchy
# Go to check bin dict, and fbin is no longer there - script fails
    startline = 0;
    endline = 0;
    source_path = os.getcwd();
    f_new = sch + "\\{0}_Integration_Report.txt".format(new_TP.name);
    f_old = sch + "\\{0}_Integration_Report.txt".format(old_TP.name);
    mos_new = {};
    mos_old = {};
    for i,line in enumerate(open(f_new)):
        if(line.startswith("<TP Modules>")):
            # print(line)
            startline = i+2;
        if(line.startswith("[TP Flow Structure]")):
            # print(line)
            endline = i-4;
    
    for i,line in enumerate(open(f_new)):
        if (i>=startline and i<=endline):
            items = line.split();
            # print(items)
            if (len(items) == 3):
                mos_new[items[0]] = items[1];
  
    for i,line in enumerate(open(f_old)):
        if(line.startswith("<TP Modules>")):
            # print(line)
            startline = i+2;
        if(line.startswith("[TP Flow Structure]")):
            # print(line)
            endline = i-4;
    
    for i,line in enumerate(open(f_old)):
        if (i>=startline and i<=endline):
            items = line.split();
            # print(items)
            if (len(items) == 3):
                mos_old[items[0]] = items[1];
    return mos_new, mos_old
    
def bin_order(x, y, hList):
# Checks if bins are the same, then if either bin is 2, then if one bin is a 4 & the other is a 5.
# If none of those conditions are met, we are left with three possibilities, good>bad, bad>good, bad>bad.
# The first two cases are dealt with by checking if the current bin is good, and returning the other bin.
# Finally, the index location of the bad bins is found in the hierarchy, and the higher priority bin is returned.
    good_bins = [str(z) for z in range(1,7)];

    #make special cases for bin 2 & 5
    # print([x,y])
    
    if (int(x) == 2 and int(y) < 7):
        return "2";
    elif (int(y) == 2 and int(x) < 7):
        return "2";
    elif (x == "4" and y == "5"):
        return y;
    elif (x == "5" and y == "4"):
        return x;
    elif (str(x) in good_bins):
        return y;
    elif (str(y) in good_bins):
        return x;
        
    #print([x,y])
    # If SDS vs SDT bad bin then take sds bin as high priority
    if int(x) > 100 and int(y) < 100:
        return y;
    elif int(x) < 100 and int(y) > 100:
        return x;
    elif int(x) > 100 and int(y) > 100:
        #Both tbins are SDT so need to get IB
        tx =x[-2:]
        ty =y[-2:]
        rankings = [hList.index(tx), hList.index(ty)]
        tm = min(rankings)
        mIdx = rankings.index(tm)
        return     [x,y][mIdx]

    rankings = [hList.index(x), hList.index(y)]
    m = min(rankings)
    mIdx = rankings.index(m)
    return     [x,y][mIdx]

def fbin_order(x, y, hList):
# The ibin of both fbin's is found, and the hierarchy is used to determine which takes priority.
# If both are the same, the first fbin takes priority, meaning the softbin is ignored.
    ibins = [x[:-2].lstrip('0'), y[:-2].lstrip('0')]
    iorder = bin_order(ibins[0], ibins[1], hList)
    idx = ibins.index(iorder)
    return [x, y][idx]

def test(old_TP,new_TP):
# Test if all the modules defined in the bin report have an mo
    bin_dict = get_bin_dict(new_TP)
    (mos_dict_new,mos_dict_old) = get_MOs_dict(old_TP,new_TP)

    for module in bin_dict.values():
        if module not in mos_dict_new.keys():
            print (module) 

def get_module_from_bin(old_TP, new_TP):
# Name says it all
    bin_dict = get_bin_dict(new_TP);
    (mos_dict_new,mos_dict_old) = get_MOs_dict(old_TP, new_TP);

    for bin in sys.argv[1:]:
        m =  bin_dict[bin]
        # print (bin, bin_dict[bin], mos_dict_new[m])
def open_B99_file():
    #Opens B99 csv file, and creates dictonary with the B99 wafer_x_y & ModuleName  
    header_path = os.getcwd();
    B99_raw_dir = header_path+"\\generated_files\\B99_raw_pull.csv";
    B99_raw = open(B99_raw_dir);
    b99_dict={}
    read = csv.DictReader(B99_raw);
    for read_row in read:
        b99_dict[read_row['WFR_X_Y']]=read_row['MODULENAME'];
    B99_raw.close();
    return (b99_dict)

def TPI_tracker(old_TP, new_TP, switch_dir, writer,do_newnew):
# The core of the script, calls all key functions & handles writing the output file.
    comp = int(old_TP.op);
    flow = "SDS";
    if ((comp >= 132350 and comp <=132365) or (comp == 132150)):
        flow = "SDT";
    
    if flow!="SDT":
        hList = get_hierarchy_list(new_TP);

    new_bin_dict = get_bin_dict(new_TP);
    old_bin_dict = get_bin_dict(old_TP);

    B99_reader=open_B99_file();

    (mos_dict_new,mos_dict_old) = get_MOs_dict(old_TP, new_TP);
    
    for i,line in enumerate(open(switch_dir)):
        items = line.strip().split(",")
        if i == 0:
            writer.writerow(["Wafer_id","sort_x","sort_y","Tray_Loc","OLD_IB","N_IB","NN_IB","OLD_FB","N_FB","NN_FB","O2N_IBSwitch","N2N_IBSWITCH","O2N_Switch","N2N_SWITCH","O2N_Module","O2N_Owner","N2N_Module","N2N_Owner","Old_Site","New_Site","NewNew_Site"]);
        else:
            # try:    
            old_ibin = items[4].lstrip('0');
            new_ibin = items[5].lstrip('0');
            new_new_ibin = items[6].lstrip('0');
            old_fbin = items[7];
            new_fbin = items[8];
            new_new_fbin = items[9];
            old_switch_owner = "0";
            new_switch_owner = "0";
                
            if flow=="SDT":
                # SDT assigns bin to newest fail bin owner (ignores newnew if untagged)
                if (old_fbin != new_fbin):
                    if (int(new_fbin) < 700):
                        old_switch_owner = old_fbin;
                    else:
                        old_switch_owner = new_fbin;
                if (new_fbin != new_new_fbin and do_newnew):
                    if (int(new_new_fbin) < 700):
                        new_switch_owner = new_fbin;
                    else:
                        new_switch_owner = new_new_fbin;
            else:
                # SDS uses the ultrabinner hierarchy instead
                if (old_fbin != new_fbin):
                    old_switch_owner = fbin_order(old_fbin, new_fbin, hList);
                if (new_fbin != new_new_fbin and do_newnew):
                    new_switch_owner = fbin_order(new_fbin, new_new_fbin, hList);
                    
            # if(i<2):
                # print(old_switch_owner);
                # print(new_switch_owner);
            owner_list = [old_switch_owner, new_switch_owner];
            module = ["0","0"];
            module_owner = ["0","0"];
            w_x_y=items[0]+"_"+items[1]+"_"+items[2]
            for j in range(0,2):
                owner_fbin = owner_list[j];
                if(owner_fbin != "0"):
                    owner_fbin = owner_fbin.zfill(4);
                    if (int(owner_fbin[:-2]) < 7):
                        module[j] = "Good Die switch";
                        module_owner[j] = "Manual switch assign required";
                    elif (owner_fbin[:-2] in ["93"]):
                        module[j] = "TP TEAM INVESTIGATE";
                        module_owner[j] = "TP TEAM";
                    elif (owner_fbin[:-2] in ["99"]):
                        print("Oooh hopefully the HW was protected");
                        try:
                            for row in B99_reader:
                                if (w_x_y in row):
                                    module[j] = B99_reader[row];
                                    try:
                                        module_owner[j] = mos_dict_new[module[j]];
                                    except:
                                        module_owner[j] = mos_dict_old[module[j]];
                                    break;
                        except:
                            module[j] = "B99 owner not found";
                            module_owner[j] = "Manual switch assign required";
                    elif (owner_fbin in ["2699","1726"]):
                        print("We got a  VADTL");
                        module[j] = "VADTL FAIL";
                        module_owner[j] = "Manual switch assign required";
                    elif (owner_fbin[:-2] in ["26"]):
                        print("HVQK acting the maggot");
                        module[j] = "Intrad-die fail";
                        module_owner[j] = "Manual switch assign required";
                    elif (owner_fbin[:-2] in ["17"]):
                        print("Stress fail at bottom step");
                        module[j] = "Stress fail at bottom step";
                        module_owner[j] = "Manual switch assign required";
                    elif (owner_fbin[:-2] in ["86"]):
                        print("STOP ADDING NEW BINS WITHOUT BEING IN THE BIN REPORT");
                        module[j] = "Combination issue, weird bin be weird";
                        module_owner[j] = "Manual switch assign required";
                    elif (int(owner_fbin) > 10000):
                        owner_fbin_mod = owner_fbin[-4:];
                        if owner_fbin_mod in new_bin_dict.keys():
                            module[j] = new_bin_dict[owner_fbin_mod]
                        else:
                            module[j] = old_bin_dict[owner_fbin_mod];
                        try:
                            module_owner[j] = mos_dict_new[module[j]];
                        except:
                            module_owner[j] = mos_dict_old[module[j]];
                    else:
                        if owner_fbin in new_bin_dict.keys():
                            module[j] = new_bin_dict[owner_fbin]
                        else:
                            module[j] = old_bin_dict[owner_fbin];
                        try:
                            module_owner[j] = mos_dict_new[module[j]];
                        except:
                            module_owner[j] = mos_dict_old[module[j]];
                                
            writer.writerow([items[0],items[1],items[2],items[3],old_ibin,new_ibin,new_new_ibin,old_fbin,new_fbin,new_new_fbin,old_ibin +">"+ new_ibin,new_ibin +">"+ new_new_ibin,old_fbin +">"+ new_fbin,new_fbin +">"+ new_new_fbin,module[0],module_owner[0],module[1],module_owner[1],items[16],items[17],items[18]]); 
            # except:
                # writer.writerow(["issue finding module/moduleowner/ibin/fbin"]);
                    
                    
