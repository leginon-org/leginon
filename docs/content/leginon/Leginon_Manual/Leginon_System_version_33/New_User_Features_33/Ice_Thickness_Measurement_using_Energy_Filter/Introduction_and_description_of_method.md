## Ice thickness using zero loss peak

The presence of an energy filter allows direct determination of the sample thickness, either through integration of the energy loss spectrum, or through comparison of filtered and unfiltered image intensities. This requires knowledge of the inelastic mean free path of the electron through the sample, which depends on voltage, objective aperture width, and sample composition. The relationship is described in equation (1), where d represents the ice thickness, I is the integrated total intensity, Izlp is the integrated zero-loss peak intensity, and Λ is the mean free path for inelastic scattering.

eq. 1: d=Λ log (Izlp/I)

We experimentally determined Λ to be 395 nm on our titan Krios microscope at NYSBC.
The node takes two images after the exposure image, the first without the energy slit and the second with the energy slit inserted. It records the average intensities of each image and performs the above calculation to determine ice thickness, in nm.

# Available in 3.4

## Ice thickness using scattering outside of the objective aperture

Ice thickness can also be estimated by measuring intensity and comparing with intensity over vacuum (Beer's law). Again a mean free path for scattering outside the objective needs to be determined. The relationship is in equation 2, where I0 is intensity over vacuum, I is image intensity, and Λ is mean free path for scattering outside of the objective aperture. The calculation takes very little time and no extra images are needed.

eq. 2: d=Λ log(I0/I)
