/*----------------------------------------------------------------------------*
*
*  scale_real_uint8.c  -  array: pixel value transfer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "scale.h"
#include "exception.h"


/* functions */

extern Status ScaleRealUint8
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param)

{
  const Real *s = src;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  scale_int_inc( uint8_t, 0, UINT8_MAX );

  return E_NONE;

}
