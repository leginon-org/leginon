/*----------------------------------------------------------------------------*
*
*  physdefs.h  -  physical constants
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef physdefs_h_
#define physdefs_h_


#include <math.h>


/* speed of light [m/s] */
#define PHYS_c (299792458e0)

/* magnetic constant [N/(A*A)] */
#define PHYS_mu0 (4*Pi*1e-7)

/* electric constant [F/m] */
#define PHYS_eps0 (1/(PHYS_mu0*PHYS_c0*PHYS_c0))

/* impedance of vacuum [Omega] */
#define PHYS_Z0 (PHYS_mu0*PHYS_c0)

/* Newtonian constant of gravitation [m*m*m/(kg*s*s)] */
#define PHYS_G (6.673e-11)

/* Planck constant [J*s] */
#define PHYS_h (6.62606876e-34)

/* Planck constant [eV*s] */
#define PHYS_heV (4.13566727e-15)

/* elementary charge [C] */
#define PHYS_e (1.602176462e-19)

/* electron mass [kg] */
#define PHYS_me (9.10938188e-31)


#endif
