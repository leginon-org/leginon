MSI-T-Tilt Application and its two-client version MSI-T-Tilt2 are designed for tilted image collection workflow.

To use it at myam-3.3 or later releases, update your myami to the current state. Then you should be able to install and run.

1.  Use [Application administration](/leginon/Leginon_Manual/Administration_Tools/Applications) myamiweb tool to import from _your-myami-git-clone_/leginon/applications/MSI-T-Tilt2.xml
2.  Run this at *you-myami-git-clone* to import the default settings for the new nodes
        python dbschema/tools/import_leginon_settings.py MSI-T-Tilt
