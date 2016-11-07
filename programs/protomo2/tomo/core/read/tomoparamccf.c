/*----------------------------------------------------------------------------*
*
*  tomoparamccf.c  -  core: retrieve parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamreadcommon.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* variables */

static const CcfParam ccftab[] = {
  { CC_XCF,   "xcf" },
  { CC_MCF,   "mcf" },
  { CC_PCF,   "pcf" },
  { CC_DBL,   "dbl" },
  { CC_UNDEF, "undefined" }
};


/* functions */

extern Status TomoparamCCF
              (Tomoparam *tomoparam,
               const char *ident,
               CcfParam *ccfparam)

{
  const char *sect;
  const char *param;
  char *str;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( ccfparam == NULL ) ) return pushexception( E_ARGVAL );

  *ccfparam = CcfParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  const CcfParam *ccfptr = ccftab;

  param = "mode";
  status = TomoparamReadScalarString( tomoparam, param, &str );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      while ( ccfptr->mode != CC_UNDEF ) {
        if ( !strcmp( str, ccfptr->ident ) ) break;
        ccfptr++;
      }
      if ( ccfptr->mode == CC_UNDEF ) {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      }
      free( str );
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {
    *ccfparam = *ccfptr;
  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}
