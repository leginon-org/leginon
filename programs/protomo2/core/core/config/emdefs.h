/*----------------------------------------------------------------------------*
*
*  emdefs.h  -  tomography: EM parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef emdefs_h_
#define emdefs_h_

#include "defs.h"
#include "mathdefs.h"
#include "physdefs.h"


/* macros */

/* convert high tension to electron wavelength */
#define LAMBDA(U) ( PHYS_h * PHYS_c / Sqrt( PHYS_e * U * ( 2.0 * PHYS_me * PHYS_c * PHYS_c + PHYS_e * U ) ) )

/* convert electron wavelength to high tension */
#define LAMBDA_TO_U(l) ( PHYS_c * ( Sqrt( PHYS_c * PHYS_c * PHYS_me * PHYS_me + PHYS_h * PHYS_h / ( ( l ) * ( l ) ) ) - PHYS_c * PHYS_me ) / PHYS_e )


/* data structures */

typedef struct {
  Coord lambda;   /* m */
  Coord cs;       /* m */
  Coord beta;     /* rad */
  Coord fs;       /* m */
} EMparam;


/* constants */

#define EMparamInitializer  (EMparam){ 0, 0, 0, 0 }


#endif
