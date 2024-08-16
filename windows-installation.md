# Instrument Windows installation

## Download poetry-build
[myami-python3](https://emg.nysbc.org/redmine/attachments/24863/leginon-py3.v300.zip)

[venv-amd64](https://emg.nysbc.org/redmine/attachments/23108/leginon-py3.venv-amd64.zip)

## 
1. copy the zip files to a directory (Desktop\Leginon-install for example)
2. unzip the files
3. unblock the folder extracted in Windows PowerShell
    1. From Windows icon, find it under “W”
    2. Do the following in Windows PowerShell at the two directories you extracted
        1. cd .\Desktop\Leginon-install\leginon-py3.v300\
        2. dir -Recurse | Unblock-File
      
## Replace the files with updated git clone
If you want to use a cloned branch from github repository, and retain its git history
1. cd your_Desktop\Leginon-install
2. git clone -b your_branch https://github.com/leginon-org/leginon.git myami-git
3. cp leginon-py3.v300\*.bat myami-git
4. Start your running using the *.bat files in myami-git instead of the ones in leginon-py3.v300

## Follow leginion.org wiki to set up config files
[leginon.org configuration on instruments](https://emg.nysbc.org/redmine/projects/leginon/wiki/Windows_Myami_Configuration)

## Running
The running of the python scripts are through batch files that sets the envir.

* To run syscheck.py, double-click syscheck.bat

* To start leginon client with launcher.py, double-click launcher.bat
