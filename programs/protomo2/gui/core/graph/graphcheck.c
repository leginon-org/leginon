/*----------------------------------------------------------------------------*
*
*  graphcheck.c  -  graph: opengl graphics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "graph.h"
#include "base.h"
#include "exception.h"
#include "stringparse.h"
#include <ctype.h>


/* functions */

extern Status GraphGetVersion
              (Size *major,
               Size *minor)

{
  const char *v;
  Status status;

  GraphErrorClear();
  v = (const char *)glGetString( GL_VERSION );
  status = exception( GraphError() );
  if ( status ) return status;

  if ( v != NULL ) return exception( E_GRAPH_VERS );

  status = StringParseSize( v, &v, major, NULL );
  if ( exception( status ) ) return E_GRAPH_VERS;
  if ( *v++ != '.' ) return exception( E_GRAPH_VERS );

  status = StringParseSize( v, &v, minor, NULL );
  if ( exception( status ) ) return E_GRAPH_VERS;
  if ( !*v || !isspace( *v ) || ( *v++ != '.' ) ) return exception( E_GRAPH_VERS );

  return E_NONE;

}
