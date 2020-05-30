# Just fucking around with the code from the notebook in: https://github.com/chervonij/DFL-Colab
# lets try to cut out lots of shit to make it just work on images 
# * run this on a google colab instance - details in COLAB.doc.md

# to run (dev) in colab:
# literally just copy and paste for now
# it will prompt you for fullface / whole face etc, just hit "wf" ( whole face) for now

# currently asked me to go to https://accounts.google.com/o/oauth2/auth?client_id=947318989803-6bn6qk8qdgf4n4g3pfee6491hc0brc4i.apps.googleusercontent.com&redirect_uri=urn%3aietf%3awg%3aoauth%3a2.0%3aoob&response_type=code&scope=email%20https%3a%2f%2fwww.googleapis.com%2fauth%2fdocs.test%20https%3a%2f%2fwww.googleapis.com%2fauth%2fdrive%20https%3a%2f%2fwww.googleapis.com%2fauth%2fdrive.photos.readonly%20https%3a%2f%2fwww.googleapis.com%2fauth%2fpeopleapi.readonly
# ???  aand enter authorization code? for google file stream



# GLOBALS?

source_url = 'https://firebasestorage.googleapis.com/v0/b/deep-fake-advertising.appspot.com/o/source-dfa.jpg?alt=media&token=43f7cfa4-6e55-4b96-8500-653057fe7ddd'
destination_url = 'https://firebasestorage.googleapis.com/v0/b/deep-fake-advertising.appspot.com/o/destination_dfa.jpg?alt=media&token=7f208561-d337-4e76-86b9-8e4b731b95d4'



# ------------------------------------------------------------------

import IPython
from google.colab import output

display(IPython.display.Javascript('''
 function ClickConnect(){
   btn = document.querySelector("colab-connect-button")
   if (btn != null){
     console.log("Click colab-connect-button"); 
     btn.click() 
     }
   
   btn = document.getElementById('ok')
   if (btn != null){
     console.log("Click reconnect"); 
     btn.click() 
     }
  }
  
setInterval(ClickConnect,60000)
'''))

print("Done.")

# Check GPU
# Google Colab can provide you with one of Tesla graphics cards: K80, T4, P4 or P100
# Here you can check the model of GPU before using DeepFaceLab
# ------------------------------------------------------------------

!nvidia-smi

# Install or update DeepFaceLab
# Install or update DeepFAceLab directly from Github
# Requirements install is automatically
# Automatically sets timer to prevent random disconnects

Mode = "install" #@param ["install", "update"]

from pathlib import Path
if (Mode == "install"):
  !git clone https://github.com/iperov/DeepFaceLab.git
 
  # fix linux warning
  # /usr/lib/python3.6/multiprocessing/semaphore_tracker.py:143: UserWarning: semaphore_tracker: There appear to be 1 leaked semaphores to clean up at shutdown
  fin = open("/usr/lib/python3.6/multiprocessing/semaphore_tracker.py", "rt")
  data = fin.read()
  data = data.replace('if cache:', 'if False:')
  fin.close()

  fin = open("/usr/lib/python3.6/multiprocessing/semaphore_tracker.py", "wt")
  fin.write(data)
  fin.close()
else:
  %cd /content/DeepFaceLab
  !git pull

!pip install -r /content/DeepFaceLab/requirements-colab.txt
!pip install --upgrade scikit-image
!apt-get install cuda-10-0

if not Path("/content/pretrain").exists():
  print("Downloading CelebA faceset ... ")
  !wget -q --no-check-certificate -r 'https://github.com/chervonij/DFL-Colab/releases/download/pretrain-CelebA/pretrain_CelebA.zip' -O /content/pretrain_CelebA.zip
  !mkdir /content/pretrain
  !unzip -q /content/pretrain_CelebA.zip -d /content/pretrain/
  !rm /content/pretrain_CelebA.zip

if not Path("/content/pretrain_Q96").exists():
  print("Downloading Q96 pretrained model ...")
  !wget -q --no-check-certificate -r 'https://github.com/chervonij/DFL-Colab/releases/download/Q96_model_pretrained/Q96_model_pretrained.zip' -O /content/pretrain_Q96.zip
  !mkdir /content/pretrain_Q96
  !unzip -q /content/pretrain_Q96.zip -d /content/pretrain_Q96/
  !rm /content/pretrain_Q96.zip

if not Path("/content/workspace").exists():
  !mkdir /content/workspace; mkdir /content/workspace/data_src; mkdir /content/workspace/data_src/aligned; mkdir /content/workspace/data_dst; mkdir /content/workspace/data_dst/aligned; mkdir /content/workspace/model  

import IPython
from google.colab import output

display(IPython.display.Javascript('''
 function ClickConnect(){
   btn = document.querySelector("colab-connect-button")
   if (btn != null){
     console.log("Click colab-connect-button"); 
     btn.click() 
     }
   
   btn = document.getElementById('ok')
   if (btn != null){
     console.log("Click reconnect"); 
     btn.click() 
     }
  }
  
setInterval(ClickConnect,60000)
'''))

print("\nDone!")

# Manage workspace
# You can import/export workspace or individual data, like model files with Google Drive
# Also, you can use HFS (HTTP Fileserver) for directly import/export you workspace from your computer
# You can clear all workspace or delete part of it
# ------------------------------------------------------------------

#@title Import from URL{ form-width: "30%", display-mode: "form" }
# URL = "http://" #@param {type:"string"}
# Mode = "unzip to content" #@param ["unzip to content", "unzip to content/workspace", "unzip to content/workspace/data_src", "unzip to content/workspace/data_src/aligned", "unzip to content/workspace/data_dst", "unzip to content/workspace/data_dst/aligned", "unzip to content/workspace/model", "download to content/workspace"]

import urllib
from pathlib import Path
  
dest_path = "/content/workspace/"

if not Path("/content/workspace").exists():
  cmd = "mkdir /content/workspace; mkdir /content/workspace/data_src; mkdir /content/workspace/data_src/aligned; mkdir /content/workspace/data_dst; mkdir /content/workspace/data_dst/aligned; mkdir /content/workspace/model"
  !$cmd

source_url_path = Path(source_url)
destination_url_path = Path(destination_url)
urllib.request.urlretrieve ( source_url, f'{dest_path}/data_src/source.png')
urllib.request.urlretrieve ( destination_url, f'{dest_path}/data_dst/destination.png')
  
print("Done!")

# detect faces
# 
# ------------------------------------------------------------------

Data = "data_src" #@param ["data_src", "data_dst"]
Detector = "S3FD" #@param ["S3FD", "S3FD (whole face)"]
Debug = False #@param {type:"boolean"}

detect_type = "s3fd"
dbg = " --output-debug" if Debug else " --no-output-debug"

folder = "workspace/"+Data
folder_aligned = folder+"/aligned"

cmd = "DeepFaceLab/main.py extract --input-dir "+folder+" --output-dir "+folder_aligned
cmd+=" --detector "+detect_type+" --force-gpu-idxs 0"+dbg

if "whole face" in Detector:
  cmd+=" --face-type whole_face" 
%cd "/content"
!python $cmd





# #@title Faceset Enhancer
# Data = "data_src" #@param ["data_src", "data_dst"]

# data_path = "/content/workspace/"+Data+"/aligned"
# cmd = "/content/DeepFaceLab/main.py facesettool enhance --input-dir "+data_path
# !python $cmd





# #@title Apply or remove XSeg mask to the faces
# Mode = "Remove mask" #@param ["Apply mask", "Remove mask"]
# Data = "data_src" #@param ["data_src", "data_dst"]

# main_path = "/content/DeepFaceLab/main.py "
# data_path = "/content/workspace/"+Data+"/aligned "
# mode_arg = "apply " if Mode == "Apply mask" else "remove "
# cmd = main_path+"xseg "+mode_arg+"--input-dir "+data_path
# cmd += "--model-dir /content/workspace/model" if mode_arg == "apply " else ""

# !python $cmd









#@title Training
Model = "SAEHD" #@param ["SAEHD", "Quick96", "XSeg"]
Backup_every_hour = True #@param {type:"boolean"}
Silent_Start = True #@param {type:"boolean"}

%cd "/content"

#Mount Google Drive as folder
from google.colab import drive
drive.mount('/content/drive')

import psutil, os, time

p = psutil.Process(os.getpid())
uptime = time.time() - p.create_time()

if (Backup_every_hour):
  if not os.path.exists('workspace.zip'):
    print("Creating workspace archive ...")
    !zip -r -q workspace.zip workspace
    print("Archive created!")
  else:
    print("Archive exist!")

if (Backup_every_hour):
  print("Time to end session: "+str(round((43200-uptime)/3600))+" hours")
  backup_time = str(3600)
  backup_cmd = " --execute-program -"+backup_time+" \"import os; os.system('zip -r -q workspace.zip workspace/model'); os.system('cp /content/workspace.zip /content/drive/My\ Drive/'); print('Backed up!') \"" 
elif (round(39600-uptime) > 0):
  print("Time to backup: "+str(round((39600-uptime)/3600))+" hours")
  backup_time = str(round(39600-uptime))
  backup_cmd = " --execute-program "+backup_time+" \"import os; os.system('zip -r -q workspace.zip workspace'); os.system('cp /content/workspace.zip /content/drive/My\ Drive/'); print('Backed up!') \"" 
else:
  print("Session expires in less than an hour.")
  backup_cmd = ""
    
cmd = "DeepFaceLab/main.py train --training-data-src-dir workspace/data_src/aligned --training-data-dst-dir workspace/data_dst/aligned --pretraining-data-dir pretrain --model-dir workspace/model --model "+Model

if Model == "Quick96":
  cmd+= " --pretrained-model-dir pretrain_Q96"

if Silent_Start:
  cmd+= " --silent-start"

if (backup_cmd != ""):
  train_cmd = (cmd+backup_cmd)
else:
  train_cmd = (cmd)

!python $train_cmd







