/*----------------------------------------------------------------------------*
*
*  textioopen.c  -  io: text file i/o
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

extern Textio *TextioOpen
               (const char *path)

{
  Textio *textio;
  FILE *stream;

  if ((path == NULL) || !*path || ((path[0] == '-') && !path[1])) {
    stream = stdin;
  } else {
    stream = fopen( path, "r" );
    if (stream == NULL) {
      pushexception(E_ERRNO);
      appendexception(", ");
      appendexception(path);
      return NULL;
    }
  }

  textio = malloc( sizeof(Textio) );
  if (textio == NULL) {
    pushexception(E_MALLOC);
  } else {
    textio->stream = stream;
    textio->linenr = 0;
    textio->stdin = (stream == stdin);
    textio->line = malloc( TextioLineinc );
    if (textio->line == NULL) {
      pushexception(E_MALLOC);
      free( textio ); textio = NULL;
    } else {
      textio->linelen = TextioLineinc;
      textio->line[0] = 0;
    }
  }

  return textio;

}
