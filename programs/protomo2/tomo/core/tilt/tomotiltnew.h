/*----------------------------------------------------------------------------*
*
*  tomotiltnew.h  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotiltnew_h_
#define tomotiltnew_h_

#include "tomotilt.h"


/* prototypes */

extern Status TomotiltNewImage
              (Tomotilt *tomotilt,
               Size axisindex,
               Size orientindex,
               Size fileindex,
               Size *imageindex);

extern Status TomotiltNewAxis
              (Tomotilt *tomotilt,
               Size *axisindex);

extern Status TomotiltNewOrient
              (Tomotilt *tomotilt,
               Size axisindex,
               Size *orientindex);

extern Status TomotiltNewFile
              (Tomotilt *tomotilt,
               const char *name,
               Size *fileindex);


#endif
