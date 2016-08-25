/*----------------------------------------------------------------------------*
*
*  base.h  -  core: initialization
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef base_h_
#define base_h_

#include "defs.h"

#define BaseName   "base"
#define BaseVers   COREVERS"."COREBUILD
#define BaseCopy   CORECOPY


/* exception codes */

enum {
  E_BASE = BaseModuleCode,
  E_INIT,
  E_IMPL,
  E_FINAL,
  E_REGISTER,
  E_MODULE,
  E_EXCEPT,
  E_DUMMY,
  E_ARGVAL,
  E_MALLOC,
  E_INTOVFL,
  E_FLTOVFL,
  E_FLTUNFL,
  E_SIGNAL,
  E_PATH,
  E_ERRNO,
  E_EOF,
  E_FILENOTFOUND,
  E_FILEEXISTS,
  E_FILEISDIR,
  E_FILENODIR,
  E_FILEACCESS,
  E_INTERNAL,
  E_USER,
  E_WARN,
  E_VAL,
  E_BASE_MAXCODE
};


/* variables */

extern const char *Main;


#endif
