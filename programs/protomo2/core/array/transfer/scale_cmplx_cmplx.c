/*----------------------------------------------------------------------------*
*
*  scale_cmplx_cmplx.c  -  array: pixel value transfer
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
#include "mathdefs.h"


/* functions */

extern Status ScaleCmplxCmplx
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param)

{
  const Cmplx *s = src;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  scale_cc_dec( Cmplx );

  return E_NONE;

}
