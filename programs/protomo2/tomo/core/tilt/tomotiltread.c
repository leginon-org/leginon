/*----------------------------------------------------------------------------*
*
*  tomotiltread.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotiltcommon.h"
#include "exception.h"


/* functions */

extern Tomotilt *TomotiltRead
                 (const char *path)

{
  Tomotilt *tomotilt = NULL;
  Parse parse;
  Status status;

  status = ParseInit( &parse, path );
  if ( exception( status ) ) return NULL;

  TomotiltParse tiltparse = TomotiltParseInitializer;
  tiltparse.parse = &parse;

  /* call parser */
  int stat = tomotilt_yyparse( &tiltparse );
  status = ParseStatus( &parse, stat );

  if ( !exception( status ) ) {
    tomotilt = tiltparse.tomotilt;
    tiltparse.tomotilt = NULL;
  }

  status = TomotiltParseFinal( &tiltparse );
  logexception( status );

  return tomotilt;

}
