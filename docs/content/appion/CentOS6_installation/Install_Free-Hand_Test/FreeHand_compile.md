**Attached to this posting there are five scripts:**

-   f90c_ubuntu64simple.csh - Compile modern Fortran programs with the gfortran compiler while linking to image2010 libraries and the FFTW library
-   f90c_ubuntu64.csh - Alternate flavor of compiler
-   fspace_subsandfuncs_modules_v1_01.f90 - Library of functions utilized by compiling script. Required to be within working directory when running f90c_ubuntu64simple.csh
-   fastfreehand_v1_01.f90 - Fortran script for Fast free-hand test. Compiles into fastfreehand_v1_01.exe
-   totsumstack.f90 - Fortran script for calculating the average image for an .mrc stack of particles

## Compiling instructions

**1.** Copy the attached scripts to your working directory.

**2.** Open and edit lines 47 - 49 of f90c_ubuntu64simple.csh to include the path to the following MRC library commands:

`<code>47: /usr/local/image2010/lib/imlib2010.a `</code>
`<code>48: /usr/local/image2010/lib/misclib.a `</code>
`<code>49: /usr/local/image2010/lib/genlib.a `</code>

**3.** Compile:

`<code>./f90c_ubuntu64simple.csh fastfreehand_v1_01.f90`</code>
`<code>./f90c_ubuntu64simple.csh totsumstack.f90 `</code>

These will compile into *fastfreehand_v1_01.exe* and *totsumstack.exe*, respectively.
