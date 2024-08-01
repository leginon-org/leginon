from distutils.core import setup
import glob
import sys

# script files to be installed in bin dir
binfiles=glob.glob('tools/*.py')
binfiles.remove('tools/__init__.py')
binfiles.extend(glob.glob('info_tools/export_all_target_info.py'))
binfiles.extend(['schema_update.py','show_schema_history.py'])
print(binfiles)
# determine if script destination has been properly specified
arg_cmd = None
arg_install_scripts = False
arg_install_dir = False
arg_help = False
print((sys.argv))
for arg in sys.argv:
	if arg == 'install':
		arg_cmd = 'install'
	if arg == 'install_scripts':
		arg_cmd = 'install_scripts'
	if 'install-scripts' in arg:
		arg_install_scripts = True
	if 'install-dir' in arg:
		arg_install_dir = True
	if 'help' in arg:
		arg_help = True
warn_user = ''
if not arg_help:
	if arg_cmd == 'install' and not arg_install_scripts:
		warn_user = '--install-scripts'
	if arg_cmd == 'install_scripts' and not arg_install_dir:
		warn_user = '--install_dir'
if warn_user:
	message = '''   *** WARNING ***
  You have not specified the option:  %s=<scriptpath>
  You are about to install %d scripts into the default script directory.
  The default could be /usr/bin, /usr/local/bin, or some other location
  you do not wish to clutter up with these scripts.

  Are you sure you want to continue? (y/n): ''' % (warn_user, len(binfiles))
	answer = input(message)
	if answer != 'y':
		print('Installation aborted.')
		sys.exit()


setup(
    name='myami-dbschema',
    version='3.3',
    description='Python scripts for leginon/appion metadata management',
    author_email='nramm@nysbc.org',
    maintainer='NRAMM',
    maintainer_email='nramm@nysbc.org',
    packages=['dbschema','dbschema.updates','dbschema.tools','dbschema.info_tools'],
    package_dir={'dbschema': ''},
		scripts=binfiles,
		)
