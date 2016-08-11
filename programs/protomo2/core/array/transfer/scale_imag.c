/*----------------------------------------------------------------------------*
*
*  scale_imag.c  -  array: pixel value transfer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transfer.h"
#include "exception.h"


/* functions */

extern Status ScaleImag
              (Type type,
               Size count,
               const void *src,
               void *dst,
               const TransferParam *param)

{
  Status status;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeImag: status = ScaleRealReal( count, src, dst, param ); break;
    default:       status = exception( E_TRANSFER_DATATYPE );
  }

  return status;

}
