  File Name                     Path                         Server       Test                              Purpose                                                                                 Install Script   Test Tool   Wizard   Added to
  ----------------------------- ---------------------------- ------------ --------------------------------- --------------------------------------------------------------------------------------- ---------------- ----------- -------- --------------------------
  syscheck.py                   myami/leginon/               Processing   Package Installation              tells you which versions of python and third party python packages you have installed   X                                     checkprocessingserver.py
  check.sh                      myami/appion/                Processing   Appion Installation               imports Appion libraries and runs binaries                                              X                X                    checkprocessingserver.py
  test1.py and test2.py         myami/leginon/                            Networking                        detect problems due to a firewall or host name resolution                               X                            X        
  createtestsession.py          myami/appion/test            Web          Image Viewer, Pipeline (Manual)   loads up a session filled with sample images for one to test with                                        X                    
  testsuite.py                  myami/appion/test            Web          Pipeline                          executes processing pipeline                                                            X                X                    
  teststack.py                  myami/appion/test            Web          Pipeline                          reads and writes stacks                                                                                  X                    
  ex1.php, ex2.php, mymrc.mrc   myami/programs/php_mrc-5.3   Web          MRC installation                  show that mrc extensions have been correctly installed                                                   X           X        checkwebserver.php

**Desired Tests**
|*.Server|*.Test|*.Purpose|*.Install Script|*.Test Tool|*.Wizard|_.Added to...|
|DB| Package Installation||X||X||
|DB| MySQL variables|make sure user modified my.cnf|||X| |
|Processing|Scipy/Numpy|make sure scipy and numpy work correctly|X|||checkProcessingServer.py|
|Processing|leginon.cfg| check that the file was created by user|X||X|checkProcessingServer.py|
|Processing|sinedon.cfg| check that the file was created by user|X||X|checkProcessingServer.py|
|Processing|EMAN Installation| check that help window is displayed|X|||checkProcessingServer.py|
|Processing|Spider Installation| launch spider|X||||
|Processing|Xmipp Installation| launch Xmipp|X|||checkProcessingServer.py|
|Web| Package Installation||X||X|checkwebserver.php|
|Web|mrc.so|check that it exists|X||X||
|Web|mrc tools| verify installation with info.php|||X|checkwebserver.php|
|Web|config.php|ensure there are no extra lines at the end after the php tag||X|X|checkwebserver.php|
