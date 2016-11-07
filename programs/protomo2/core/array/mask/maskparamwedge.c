/*----------------------------------------------------------------------------*
*
*  maskparamwedge.c  -  array: mask operations
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

extern MaskParam *MaskParamWedge
                  (Coord *A,
                   Coord *b,
                   Coord *wedge,
                   Coord val,
                   Size wedgedef,
                   MaskFlags flags,
                   MaskParam *param)


{

  MaskParam *ptr = MaskParamNew( &param );
  if ( ptr == NULL ) { pushexception( E_MALLOC ); return NULL; }

  ptr->A = A;
  ptr->b = b;

  if ( wedgedef ) {

    ptr->flags = MaskFunctionWedge;

  } else {

    ptr->flags = MaskFunctionNone;
    wedge = NULL;

  }

  ptr->wid = wedge;
  ptr->apo = NULL;
  ptr->val = val;
  ptr->flags |= flags & MaskModeMask;

  ptr++;
  ptr->flags = MaskFunctionNone;

  return param;

}
