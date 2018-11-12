/*----------------------------------------------------------------------------*
*
*  textiocommon.h  -  io: text file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef textiocommon_h_
#define textiocommon_h_

#include "textio.h"
#include <stdio.h>


/* macros */

#define TextioLineinc 32


/* types */

struct _Textio {
  FILE *stream;
  char *line;
  Size linelen;
  Size linenr;
  Bool stdin;
};


#endif
