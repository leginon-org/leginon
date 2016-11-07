/*----------------------------------------------------------------------------*
*
*  parseerror.c  -  core: auxiliary parser routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "parse.h"
#include "exception.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* functions */

static void ParseErrorLoc
            (const Parse *parse,
             const ParseLoc *loc)

{
  Size i;

  Size line = loc->line;
  if ( !line ) return;

  char msg[64];
  sprintf( msg, " at line %"SizeU, line );
  appendexception( msg );

  char *buf = ParseGetBuf( parse, line );
  if ( ( buf != NULL ) && ( loc->pos > 0 ) ) {
    Size length = strlen( buf );
    char *msg1 = malloc( length + loc->pos + 4 );
    if ( msg1 != NULL ) {
      msg1[0] = '\n';
      memcpy( msg1 + 1, buf, length );
      char *msg2 = msg1 + 1 + length;
      msg2[0] = '\n';
      for ( i = 1; i < loc->pos; i++ ) {
        msg2[i] = isspace( msg1[i] ) ? msg1[i] : ' ';
      }
      msg2[i++] = '^';
      msg2[i++] = 0;
    }
    appendexception( msg1 );
    free( msg1 );
  }

}


extern void ParseError
            (Parse *parse,
             const ParseLoc *loc,
             Status status)

{

  if ( parse == NULL ) {
    pushexception( E_PARSE ); return;
  }

  if ( !status || ( loc == NULL ) ) {
    pushexception( E_PARSE );
    if ( !status ) status = E_PARSE;
  }

  pushexception( status );
  ParseErrorLoc( parse, loc );

  if ( !parse->status ) parse->status = status;

}
