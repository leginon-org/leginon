/*----------------------------------------------------------------------------*
*
*  tomoparamdebug.c  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamdebug.h"
#include "exception.h"


/* functions */

extern Status TomoparamDumpVar
              (const Tomoparam *tomoparam)

{
  Status status;

  TomoparamVar *var = tomoparam->vartab;
  if ( ( var == NULL ) && tomoparam->varlen ) {
    return exception( E_TOMOPARAM );
  }

  for ( Size i = 0; i < tomoparam->varlen; i++, var++ ) {

    status = TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );
    if ( exception( status ) ) return status;

  }

  return E_NONE;

}
