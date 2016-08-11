/*----------------------------------------------------------------------------*
*
*  textioclose.c  -  io: text file i/o
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

extern Status TextioClose
              (Textio *textio)

{

  if (textio == NULL) {
    return exception(E_ARGVAL);
  }

  if (!textio->stdin) {
    fclose( textio->stream );
  }

  free( textio->line );
  free( textio );

  return E_NONE;

}
