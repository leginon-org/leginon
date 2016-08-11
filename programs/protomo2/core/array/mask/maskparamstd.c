/*----------------------------------------------------------------------------*
*
*  maskparamstd.c  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "maskparam.h"
#include "exception.h"


/* functions */

extern MaskParam *MaskParamStd
                  (Coord *A,
                   Coord *b,
                   Coord *width,
                   Coord *sigma,
                   Coord val,
                   Size rectdef,
                   Size ellipsdef,
                   Size sigmadef,
                   MaskFlags flags,
                   MaskParam *param)


{

  MaskParam *ptr = MaskParamNew( &param );
  if ( ptr == NULL ) { pushexception( E_MALLOC ); return NULL; }

  ptr->A = A;
  ptr->b = b;
  ptr->flags = MaskFunctionNone;

  if ( rectdef || ellipsdef ) {

    if ( width == NULL ) {
      sigma = NULL;
    } else {
      ptr->flags = rectdef ? MaskFunctionRect : MaskFunctionEllips;
      if ( sigmadef && ( sigma != NULL ) ) {
        ptr->flags |= MaskModeApod;
      }
    }

  } else if ( sigmadef ) {

    if ( sigma != NULL ) {
      ptr->flags = MaskFunctionGauss;
    }
    width = sigma;
    sigma = NULL;

  } else {

    width = NULL;
    sigma = NULL;

  }

  ptr->wid = width;
  ptr->apo = sigma;
  ptr->val = val;
  ptr->flags |= flags & MaskModeMask;

  ptr++;
  ptr->flags = MaskFunctionNone;

  return param;

}
