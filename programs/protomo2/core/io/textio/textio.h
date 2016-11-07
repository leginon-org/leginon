/*----------------------------------------------------------------------------*
*
*  textio.h  -  io: text file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef textio_h_
#define textio_h_

#include "iodefs.h"
#include "stringparse.h"

#define TextioName   "textio"
#define TextioVers   IOVERS"."IOBUILD
#define TextioCopy   IOCOPY


/* exception codes */

enum {
  E_TEXTIO = TextioModuleCode,
  E_TEXTIO_READ,
  E_TEXTIO_MAXCODE
};


/* types */

struct _Textio;

typedef struct _Textio Textio;


/* prototypes */

extern Textio *TextioOpen
               (const char *path);

extern Status TextioReadline
              (Textio *textio,
               char **line,
               Size *linenr);

extern Status TextioReadlist
              (Textio *textio,
               StringParse parse,
               Size fieldcount,
               void **list,
               Size *count);

extern Status TextioClose
              (Textio *textio);

extern Status TextioImportList
              (const char *path,
               StringParse parse,
               Size fieldcount,
               void **list,
               Size *count);


#endif
