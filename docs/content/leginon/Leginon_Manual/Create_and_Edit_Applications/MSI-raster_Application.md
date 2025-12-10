The basic flow of "MSI-raster" is the same as other MSI applications. HoleFinder class nodes are replaced with RasterFinder in the application. Node aliases that refer to Hole are replaced with Sub-square. The bindings of the corresponding nodes are the same as those in MSI-Edge and MSI-T.

### Table 18.5. MSI-raster Nodes:

  Node Class:               Node alias:            Launcher:
  ------------------------- ---------------------- -----------
  EM                        Instrument             scope
  PresetsManager            Presets Manager        main
  DriftManager              Drift Manager          main
  MosaicClickTargetFinder   Square Targeting       main
  Acquisition               Grid                   main
  MosaicTargetMaker         Grid Targeting         main
  Navigator                 Navigation             main
  Corrector                 Correction             main
  Acquisition               Square                 main
  Acquisition               Sub-square             main
  RasterFinder              Exposure Targeting     main
  RasterFinder              Sub-square Targeting   main
  FFTMaker                  Focus FFT              main
  Focuser                   Z Focus                main
  Focuser                   Focus                  main
  FFTMaker                  Exposure FFT           main
  Acquisition               Exposure               main

[< "MSI-T" Application](/leginon/Leginon_Manual/Create_and_Edit_Applications/MSI-T_Application) | ["MSI-Tomography" Application >](/leginon/Leginon_Manual/Create_and_Edit_Applications/MSI-Tomography_Application)
