/*----------------------------------------------------------------------------*
*
*  textioimportlist.c  -  io: text file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "textiocommon.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TextioImportList
              (const char *path,
               StringParse parse,
               Size fieldcount,
               void **list,
               Size *count)

{
  Status status;

  Textio *textio = TextioOpen( path );
  status = testcondition( textio == NULL );
  if ( status ) return status;

  status = TextioReadlist( textio, parse, fieldcount, list, count );
  if ( exception( status ) ) {
    exception( TextioClose( textio ) );
    return status;
  }

  status = TextioClose( textio );
  if ( exception( status ) ) {
    free( *list ); *list = NULL;
    return status;
  }

  return E_NONE;

}
