/*----------------------------------------------------------------------------*
*
*  signals.h  -  core: signals
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef signals_h_
#define signals_h_

#include "defs.h"


/* variables */

extern int SignalInterrupt;

extern int SignalCatch;


/* prototypes */

extern Status SignalInit();

extern Status SignalSet();

extern Status SignalRestore();

extern const char *SignalString
                   (int sig);


#endif
