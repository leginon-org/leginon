## Upload MSI-Ptolemy application into leginon database

Follow the instruction in [web application tools](/leginon/Leginon_Manual/Administration_Tools/Applications)

-   Note: If your system needs two Leginon client opened, each on a different pc, use MSi-Ptolemy2.xml

If you have your own application you can do the following replacement by [editing your application](/leginon/Leginon_Manual/Create_and_Edit_Applications/Use_the_Application_Editor_to_create_Leginon_applications) :

Square Targeting Node : MosaicClickTargetFinder class => MosaicScoreTargetFinder
Exposure Targeting Node: JAHCFinder => ScoreTargetFinder
