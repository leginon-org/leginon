/*----------------------------------------------------------------------------*
*
*  peak_real.c  -  array: spatial operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spatial.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status PeakReal
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               Size *ipos,
               Coord *pos,
               void *pk,
               const PeakParam *param)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( dim ) {
    case 1:  status = exception( Peak1dReal( srclen, srcaddr, ipos, pos, pk, param ) ); break;
    case 2:  status = exception( Peak2dReal( srclen, srcaddr, ipos, pos, pk, param ) ); break;
    case 3:  status = exception( Peak3dReal( srclen, srcaddr, ipos, pos, pk, param ) ); break;
    default: status = exception( E_SPATIAL );
  }

  return status;

}
