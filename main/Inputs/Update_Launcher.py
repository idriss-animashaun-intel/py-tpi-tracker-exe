import os
import urllib.request
import zipfile
import shutil
import time


TPI_tracker_master_directory = os.getcwd()
TPI_tracker_file = TPI_tracker_master_directory+"\\TPI_Tracker.exe"
Old_TPI_tracker_directory = TPI_tracker_master_directory+"\\py_tpi_tracker_exe-master"

proxy_handler = urllib.request.ProxyHandler({'https': 'http://proxy-dmz.intel.com:912'})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

def installation():
    urllib.request.urlretrieve("https://github.com/idriss-animashaun-intel/py-tpi-tracker-exe/archive/refs/heads/main.zip", TPI_tracker_master_directory+"\\TPI_tracker_luancher_new.zip")
    print("*** Updating Launcher Please Wait ***")
    zip_ref = zipfile.ZipFile(TPI_tracker_master_directory+"\TPI_tracker_luancher_new.zip", 'r')
    zip_ref.extractall(TPI_tracker_master_directory)
    zip_ref.close()
    os.remove(TPI_tracker_master_directory+"\TPI_tracker_luancher_new.zip")

    src_dir = TPI_tracker_master_directory + "\\py-tpi-tracker-exe-main"
    dest_dir = TPI_tracker_master_directory
    fn = os.path.join(src_dir, "TPI_Tracker.exe")
    shutil.copy(fn, dest_dir)

    shutil.rmtree(TPI_tracker_master_directory+"\\py-tpi-tracker-exe-main")

    time.sleep(5)
    
def upgrade():
    print("*** Updating Launcher Please Wait ***")    
    print("*** Removing old files ***")
    time.sleep(20)
    os.remove(TPI_tracker_file)
    time.sleep(10)
    installation()


### Is TPI_tracker already installed? If yes get file size to compare for upgrade
if os.path.isfile(TPI_tracker_file):
    local_file_size = int(os.path.getsize(TPI_tracker_file))
    # print(local_file_size)
    ### Check if update needed:
    f = urllib.request.urlopen("https://github.com/idriss-animashaun-intel/py-tpi-tracker-exe/raw/main/TPI_Tracker.exe") # points to the exe file for size
    i = f.info()
    web_file_size = int(i["Content-Length"])
    # print(web_file_size)

    if local_file_size != web_file_size:# upgrade available
        upgrade()

### TPI_tracker wasn't installed, so we download and install it here                
else:
    installation()

if os.path.isdir(Old_TPI_tracker_directory):
        print('removing py_tpi_tracker_exe-master')
        time.sleep(5)
        shutil.rmtree(Old_TPI_tracker_directory)

print('Launcher up to date')