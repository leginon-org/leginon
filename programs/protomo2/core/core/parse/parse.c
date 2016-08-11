/*----------------------------------------------------------------------------*
*
*  parse.c  -  core: auxiliary parser routines
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
#include <stdlib.h>
#include <string.h>



/* functions */

extern Status ParseInit
              (Parse *parse,
               const char *path)

{
  FILE *handle = NULL;

  if ( ( path != NULL ) && *path && strcmp( path, "-" ) ) {

    handle = fopen( path, "r"  );
    if ( handle == NULL ) {
      return pushexceptionmsg( E_ERRNO, ", ", path );
    }

  }

  *parse = ParseInitializer;

  parse->handle = handle;

  return E_NONE;

}


extern Status ParseFinal
              (Parse *parse)

{
  Status status = E_NONE;

  if ( parse != NULL ) {

    if ( parse->status != E_PARSE_NO ) {
      ParseReset( parse );
    }

    if ( parse->handle != NULL ) {
      if ( fclose( parse->handle ) ) {
        status = exception( E_ERRNO );
      }
      parse->handle = NULL;
    }

  }

  return status;

}


extern Status ParseStatus
              (Parse *parse,
               int retstat)

{
  Status status;

  if ( parse == NULL ) return pushexception( E_ARGVAL );

  if ( parse->level ) {
    ParseError( parse, &parse->locc, E_PARSE_UNCOM );
  }

  status = parse->status;

  if ( status == E_PARSE_NO ) {
    pushexception( status );
  } else if ( retstat ) {
    if ( !status ) status = pushexception( E_PARSE );
  } else {
    if ( status ) status = pushexception( E_PARSE );
  }

  ParseReset( parse );

  return status;

}


static void ParseBufReset
            (ParseBuf *buf)

{

  if ( buf->ptr != NULL ) free( buf->ptr );

  *buf = ParseBufInitializer;

}


extern void ParseReset
            (Parse *parse)

{

  if ( parse != NULL ) {

    ParseBufReset( &parse->buf );
    ParseBufReset( &parse->bufp );
    parse->locp = ParseLocInitializer;
    parse->level = 0;
    parse->status = E_PARSE_NO;

  }

}


extern char *ParseGetBuf
             (const Parse *parse,
              Size line)

{

  if ( parse != NULL ) {

    if ( parse->buf.ptr != NULL ) {
      if ( line == parse->buf.loc.line ) return parse->buf.ptr;
    }

    if ( parse->bufp.ptr != NULL ) {
      if ( line == parse->bufp.loc.line ) return parse->bufp.ptr;
    }

  }

  return NULL;

}
