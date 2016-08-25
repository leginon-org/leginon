/*----------------------------------------------------------------------------*
*
*  textioreadline.c  -  io: text file i/o
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

extern Status TextioReadline
              (Textio *textio,
               char **line,
               Size *linenr)

{
  enum { begin, normal, comment } state;
  Size len, pos;

  if (textio == NULL) return exception(E_ARGVAL);
  if (line == NULL) return exception(E_ARGVAL);

  state = begin;
  len = 0;
  textio->linenr++; pos = 0;

  while (True) {

    int c = getc( textio->stream );
    if (ferror( textio->stream )) {
      logexception(E_ERRNO);
      break;
    }
    if (feof( textio->stream )) {
      if (pos) break;
      *line = NULL;
      if (linenr != NULL) *linenr = textio->linenr;
      return E_NONE;
    }

    if (c == '\n') {
      if (state == normal) {
        textio->line[len] = 0;
        *line = textio->line;
        if (linenr != NULL) *linenr = textio->linenr;
        return E_NONE;
      }
      len = 0;
      textio->linenr++; pos = 0;
      state = begin;
      continue;
    }

    pos++;
    if (state == begin) {
      if (c == ' ') continue;
      if (c == '\t') continue;
      if ((c == '#') || (c == '!')) {
        state = comment;
        continue;
      }
      state = normal;
    }

    textio->line[len++] = c;
    if (len >= textio->linelen) {
      char *line = realloc( textio->line, textio->linelen + TextioLineinc );
      if (line == NULL) {
        logexception(E_MALLOC);
        len = textio->linelen - 1;
        break;
      }
      textio->line = line;
      textio->linelen += TextioLineinc;
    }

  }

  textio->line[len] = 0;
  *line = textio->line;
  if (linenr != NULL) *linenr = textio->linenr;

  return exception(E_TEXTIO_READ);

}
