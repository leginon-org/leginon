/*----------------------------------------------------------------------------*
*
*  tomotiltcommon.c  -  tomography: tilt series
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

extern Status TomotiltParseInit
              (TomotiltParse *tiltparse,
               const char *ident)

{
  Status status;

  tiltparse->tomotilt = TomotiltCreate( ident, 0, 0, 0, 0, NULL );
  status = testcondition( tiltparse->tomotilt == NULL );

  tiltparse->state = STATE_PARAM;

  tiltparse->parse->status = status;

  return status;

}


extern Status TomotiltParseFinal
              (TomotiltParse *tiltparse)

{
  Parse *parse = tiltparse->parse;
  Status status;

  if ( tiltparse->tomotilt != NULL ) {
    TomotiltDestroy( tiltparse->tomotilt );
  }

  status = ParseFinal( tiltparse->parse );
  logexception( status );

  *tiltparse = TomotiltParseInitializer;

  tiltparse->parse = parse;

  return status;

}
