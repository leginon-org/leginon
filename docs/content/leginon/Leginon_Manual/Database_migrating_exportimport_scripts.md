When you need to move all your data in the database to a new computer, you can

Either

stop mysqld and copy all database files over (located, by default, in /var/lib/mysql). This only works well if your new computer is identical in setup.

Or

1.  do a full [mysqldump](/leginon/Leginon_Manual/Trouble_shooting/Mysqldump_of_your_database) which includes instruction on how to recreate it through mysql command and then
2.  [restore it](/leginon/Leginon_Manual/Trouble_shooting/Load_mysqldumped_databases) on the new host

## Start fresh but keep the instruments/calibrations/settings even most recent gain/dark references and other tables that you really care.

As years goes by, the databases get too big to backup or congested with old instrument and images you no longer own or care. A few scripts were written to
make it possible to take a clean installation and migrate from the old system the stuff you need to care over.

  ---------------------------- ------------------------------- -------------------------------
  what                         export                          import
  tem,mag table, camera        export_leginon_instruments.py   import_leginon_instruments.py
  calibrations                 export_leginon_cal.py           import_leginon_cal.py
  leginon settings             export_leginon_settings.py      import_leginon_settings.py
  presets                      export_leginon_presets.py       import_leginon_presets.py
  gain/dark reference images   export_leginon_ref.py           import_leginonref.py
  ---------------------------- ------------------------------- -------------------------------

The old databases can be kept as archive that you can still view with its own myamiweb but no longer write to.

These are in myami/dbschema/tools. They are not installed by the auto-installer, so you do need a git clone myami to access it.
You also need to know your sinedon.cfg of the system you migrate from and to.

## Step 1: Use mysqldump to migrate single tables (see above and mysql documentation on the internet) and restore them on the new host.

Here are the ones you might want:
1. all projectdb except the two tables projectexperiments and processingdb (You can dump/restore the whole database and then empty the data in these two tables).
2. leginondb tables GroupData and UserData

If you want all old applications, you can also dump/import ApplicationData. Otherwise, individual application import/export is easiest using myamiweb administration tab.

## Step 2: On the old system, run these in a clean directory

For example, a subdirectory from myami/dbschema/tools

source_database_hostname is what is in your sinedon.cfg
All output files except reference images are json files. The name format is used for parsing in the import.

### export_leginon_instruments.py

**Usage** export_leginon_instruments.py source_database_hostname <hostname1,hostname2>
(optional hostname1, hostname2 etc are specific instrument hostname to export. default will export all)
**Example** python ../export_leginon_instruments.py localhost Titan123456,GatanK3host

### export_leginon_cal.py

**Usage** export_leginon_cal.py source_database_hostname source_camera_hosthame camera_name `<source_tem_name>
**Example** python ../export_leginon_cal.py localhost GatanK3host k3host EFKrios

### export_leginon_settings.py

This export settings used by a specific session, typically a session you know containing good settings to be used as default in your new system.

**Usage** python export_leginon_settings.py `<sessionname> `<optional partial application name> `<optional node name prefix>
**Example** python ../export_leginon_settings.py 20dec31a

### export_leginon_presets.py

This export presets used of a specific session, typically the same session as above to be used as default in your new system. It general files separated by tem/camera combo.

**Usage** python export_leginon_presets.py `<sessionname> `<optional partial application name> `<optional node name prefix>
**Example** python ../export_leginon_presets 20dec31a

### export_leginon_ref.py

**Usage** python export_leginon_ref.py source_database_hostname source_camera_hosthame camera_name
**Example** python ../export_leginon_ref.py localhost k3host GatanK3

This script and its import counter part are also used as a regular backup to quickly recover from file server issue that require us to use a different file disk and avoid accessing the problem disk.

## Step 3: copy the resulting json and mrc files to the new leginon host (called new_host in the examples)

## Step 4: On the clean installation that has already administrator user and other default in the installation, run these imports on the json files.

### import_leginon_instruments.py

**Usage** import_leginon_instruments.py database_hostname
**Example** python ../import_leginon_instruments.py new_host

### import_leginon_cal.py

**Usage** import_leginon_cal.py database_hostname camera_cal_json_file
**Example** python ../import_leginon_cal.py new_host cal_titan123456+EFKrios+gatank3host+GatanK3.json

### import_leginon_settings.py

**Usage** python import_leginon_settings.py `<applicationname or json filepath>
**Example** python ../import_leginon_settings.py 20dec31a.json

### import_leginon_presets.py

**Usage** python import_leginon_presets.py database_hostname tem_camera_presets_json_file
**Example** ../python import_leginon_presets.py new_host preset_titan123456+EFKrios+gatank3host+GatanK3.json

### import_leginon_ref.py

**Usage** import_leginon_ref.py database_hostname camera_ref_json_file
**Example** python ../import_leginon_ref.py new_host ref_titan123456+EFKrios+gatank3host+GatanK3.json
