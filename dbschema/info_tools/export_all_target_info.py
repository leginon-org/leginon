#!/usr/bin/env python
from dbschema.info_tools import export_targets
from dbschema.info_tools import export_ice
from dbschema.info_tools import export_ctf
from dbschema.info_tools import export_child_paths
from dbschema.info_tools import export_frame_drift

if __name__=='__main__':
	session_name = input('Which session ? ')
	base_path = input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app_target = export_targets.TargetExporter(session_name, base_path)
	app_ice = export_ice.IceThicknessExporter(session_name, base_path)
	app_ctf = export_ctf.CtfExporter(session_name, base_path)
	app_image = export_child_paths.ChildImagePathExporter(session_name, base_path)
	app_drift = export_frame_drift.DDExporter(session_name, base_path)
	app_target.run()
	app_ice.run()
	app_ctf.run()
	app_drift.run()
	print(('All Done! Saved in %s' % (base_path,)))
