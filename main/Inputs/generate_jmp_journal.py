import sys
import xml.etree.ElementTree
import os
import csv
import subprocess
from os.path import expanduser
import re
from .resource_path import resource_path


# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
#     base_path = re.sub(r"Inputs+$","",base_path,flags=re.I); #RC replaced split with regex to remove Inputs folder from folder path (avoid losing the I on I drive.)
#     return os.path.join(base_path, relative_path)



try:
    from Inputs import PiUber
except:
    from TPITracker.Inputs import PiUber

python_exe = sys.executable
#if sys.version_info >= (3,0,0):
try:
    import pip
except:
    print("need to import pip");
    subprocess.call(python_exe +' Inputs/pip/get-pip.py --proxy="http://proxy-chain.intel.com:911"')
    import pip

def __init__():
    letsgo=1;

def generate_jmp_journal(site,schema,old_TP,new_TP,newnew_TP,flow,do_newnew):
   # The core function of this script. It creates & calls 3 scripts
   # 1. Pull the raw data
   # 2. Pull the HVQK data (for SDS/Sort only!)
   # 3. Create a generic jmp script which passes in some key variables, then calls the core jmp
   # script. This jmp script generates the full jmp journal & lots of output docs (including
   # HVQK application rate & Test Time script)
    home = expanduser("~");
    source_path = os.getcwd();
    
    if (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\11\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\11\\jmp.exe";
    elif (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\12\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\12\\jmp.exe";
    elif (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\13\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\13\\jmp.exe";
    elif (os.path.exists("C:\\Program Files\\SAS\\JMPPRO\\14\\jmp.exe")):
        jmpdir = "C:\\Program Files\\SAS\\JMPPRO\\14\\jmp.exe";
        print("I have not fully validated JMP 14, so if it breaks... I blame them and them alone.");
    else:
        print("You don't have JMP 11-14, you're pretty screwed :( ");

    jmpscript = source_path+"\\generated_files\\jmp_tmp.jsl";

    print("Pulling SQL for jmp");
    script_input_path = source_path+"/generated_files/pull_raw_kappa_data.aws";
    output_path = source_path+"/generated_files/pull_raw_kappa_data.csv";
    hvqk_path = source_path+"/generated_files/pull_hvqk_data.csv";
    vmu_path = source_path+"/generated_files/pull_vmu_data.csv";
    
    tbin_enabled = generate_raw_data_sql_file(site,schema,old_TP,new_TP,newnew_TP,flow,output_path,do_newnew);
    
    comp = int(old_TP.op);
    if ((comp < 132350 or comp > 132365) and (comp != 132150)):
        # Basically if not SDT...
        generate_hvqk_app_sql_file(site,schema,old_TP,new_TP,newnew_TP,flow,hvqk_path,do_newnew);
        
    generate_vmu_sql_file(site,schema,new_TP,flow,vmu_path);

    temp_jmp_script(old_TP,new_TP,newnew_TP,flow,tbin_enabled);

    print("Doing JMP");
    check_source = os.path.splitdrive(home);
    if(check_source[0] == r"C:"):
        print("Running jmp from local computer");
        header_path = os.getcwd();
        subprocess.call(resource_path("..\\JMPbackgroundcaller.exe") + " generated_files\\jmp_tmp.jsl",shell = False);
    else:
        print("Running jmp from scripthost");
        subprocess.call(r"\\SHUser-prod.intel.com\SHprodUser$\eoghanoc\eoghanoc_scripthost\TPI_Tracker\Inputs\generated_files\main_jmp.exe");
    print("JMP complete");

    return tbin_enabled

def temp_jmp_script(old_TP,new_TP,newnew_TP,flow,tbin_enabled):
    print("Generating JMP script");
    source_path = resource_path("");
    source_path = source_path.replace('c:', 'C:');
    source_path = source_path.replace('Inputs', '');
    header_path = os.getcwd();
    input_path = resource_path("sql_files\\jmpCreator.txt");

    if tbin_enabled==1:
        input_path = resource_path("sql_files\\jmpCreatorTbin.txt");
    else:
        input_path = resource_path("sql_files\\jmpCreator.txt");

    output_path = header_path + "\\generated_files\\jmp_tmp.jsl";
    # print(source_path);
    
    oop = old_TP.engID+"_"+old_TP.op;
    nop = new_TP.engID+"_"+new_TP.op;
    nnop = newnew_TP.engID+"_"+newnew_TP.op;

    comp = int(old_TP.op);
    if ((comp >= 132350 and comp <=132365) or (comp == 132150)):
        flow = "SDTSORT";
    else:
        flow = "SORT";
        
    with open(input_path, 'r') as file : # Read in the default sql script
      jmp_script = file.read()
      
    jmp_script = jmp_script.replace('##OENG##', old_TP.engID)# Replace the EngID
    jmp_script = jmp_script.replace('##NENG##', new_TP.engID)# Replace the EngID
    jmp_script = jmp_script.replace('##NNENG##', newnew_TP.engID)# Replace the EngID
    
    jmp_script = jmp_script.replace('##OENGOP##', oop)# Replace the EngID_OP
    jmp_script = jmp_script.replace('##NENGOP##', nop)# Replace the EngID_OP
    jmp_script = jmp_script.replace('##NNENGOP##', nnop)# Replace the EngID_OP

    jmp_script = jmp_script.replace('##FLOW##',flow )# Replace the flow
    jmp_script = jmp_script.replace('##RP##',os.path.dirname(source_path)+"\\" )# Replace the flow

    out = open(output_path,'w');
    out.write(jmp_script);
    out.close;
    print("JMP script created");

def generate_vmu_sql_file(site,schema,new_TP,flow,output_path):
    print('Generating VMU pull');
    header_path = os.getcwd();
    sql_input_path = resource_path("sql_files\\vmuPull.txt")
    sql_output_path = header_path + "\\generated_files\\pull_vmu_data.aws";
    
    format_operations = '\'' + str(new_TP.op) + '\'';
    format_eng_IDs = '\'' + str(new_TP.engID) + '\'';

    with open(sql_input_path, 'r') as file : # Read in the default sql script
      uber_script = file.read()

    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the operations
    uber_script = uber_script.replace('##OPERATIONS##', format_operations)# Replace the eng_id_list
    
    with open(sql_output_path, 'w') as file: # Write the file out again
      file.write(uber_script);
      
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site));
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(output_path);
    print('VMU pull complete');

def generate_raw_data_sql_file(site,schema,old_TP,new_TP,newnew_TP,flow,output_path,do_newnew):
    print("Generating Bin data SQL pull");
    header_path = os.getcwd();
    sql_input_path = resource_path("sql_files\\generateJmpJournalPull.txt");
    sql_output_path = header_path + "\\generated_files\\pull_raw_kappa_data.aws";
    operation_list = [];
    eng_IDs_list = [];
    
    operation_list = operation_list + ['\'' + str(old_TP.op) + '\''];
    operation_list = operation_list + ['\'' + str(new_TP.op) + '\''];
    if do_newnew:
        operation_list = operation_list + ['\'' + str(newnew_TP.op) + '\''];

    eng_IDs_list = eng_IDs_list + ['\'' + str(old_TP.engID) + '\''];
    eng_IDs_list = eng_IDs_list + ['\'' + str(new_TP.engID) + '\''];
    if do_newnew:
        eng_IDs_list = eng_IDs_list + ['\'' + str(newnew_TP.engID) + '\''];

    format_operations = (','.join(map(str, operation_list))) ## format operations list
    format_eng_IDs = (','.join(map(str, eng_IDs_list))) ## format Eng ID list

    with open(sql_input_path, 'r') as file : # Read in the default sql script
      uber_script = file.read()
      
    uber_script = uber_script.replace('##FLOW##', flow)# Replace the operations
    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the operations
    uber_script = uber_script.replace('##OPERATIONS##',format_operations )# Replace the eng_id_list
    
    with open(sql_output_path, 'w') as file: # Write the file out again
      file.write(uber_script);
      
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site));
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(output_path);
    print("Bin data SQL pull complete");

    tbin_enabled = tbin_checker(output_path);
    return tbin_enabled

def generate_hvqk_app_sql_file(site,schema,old_TP,new_TP,newnew_TP,flow,output_path,do_newnew):
    print("Generating HVQK SQL pull");
    header_path = os.getcwd();
    sql_input_path = resource_path("sql_files\\hvqkPull.txt");
    sql_output_path = header_path + "\\generated_files\\pull_hvqk_data.aws";

    operation_list = [];
    eng_IDs_list = [];
    
    operation_list = operation_list + ['\'' + str(old_TP.op) + '\''];
    operation_list = operation_list + ['\'' + str(new_TP.op) + '\''];
    if do_newnew:
        operation_list = operation_list + ['\'' + str(newnew_TP.op) + '\''];

    eng_IDs_list = eng_IDs_list + ['\'' + str(old_TP.engID) + '\''];
    eng_IDs_list = eng_IDs_list + ['\'' + str(new_TP.engID) + '\''];
    if do_newnew:
        eng_IDs_list = eng_IDs_list + ['\'' + str(newnew_TP.engID) + '\''];

    format_operations = (','.join(map(str, operation_list))) ## format operations list
    format_eng_IDs = (','.join(map(str, eng_IDs_list))) ## format Eng ID list

    with open(sql_input_path, 'r') as file : # Read in the default sql script
      uber_script = file.read()

    uber_script = uber_script.replace('##ENG_IDS##', format_eng_IDs)# Replace the operations
    uber_script = uber_script.replace('##OPERATIONS##',format_operations )# Replace the eng_id_list
    uber_script = uber_script.replace('##FLOW##',flow )# Replace the flow
    
    with open(sql_output_path, 'w') as file: # Write the file out again
      file.write(uber_script);
      
    conn = PiUber.connect(datasource=("%s_PROD_ARIES" % site));
    curr = conn.cursor();
    curr.execute(uber_script);
    curr.to_csv(output_path);
    print("HVQK SQL pull complete");

def tbin_checker(output_path):
    tbin_enabled =0;
    count =0
    for i,line in enumerate(open(output_path)):
        items = line.strip().split(",");
        old_ftbin = items[6];
        if (i!=0):
            count = count + int(old_ftbin);
    if count > 0:
        tbin_enabled = 1;

    return tbin_enabled

