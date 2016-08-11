/*----------------------------------------------------------------------------*
*
*  tomoimageset.c  -  align: image geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoimage.h"
#include "mat2.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Status TomoimageSet
              (TomoimageList *list,
               Coord Ap[3][2],
               TomoimageFlags flags)

{
  Coord Ap1[2][2];
  Status status;

  if ( argcheck( list == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( Ap == NULL ) ) return exception( E_ARGVAL );

  status = Mat2Inv( Ap, Ap1, NULL );
  if ( exception( status ) ) return status;

  Coord s20 = list->A[2][0] * Ap1[0][0] + list->A[2][1] * Ap1[1][0];
  Coord s21 = list->A[2][0] * Ap1[0][1] + list->A[2][1] * Ap1[1][1];

  list->S[0][0] = 1;   list->S[0][1] = 0;   list->S[0][2] = list->A[0][2]; 
  list->S[1][0] = 0;   list->S[1][1] = 1;   list->S[1][2] = list->A[1][2]; 
  list->S[2][0] = s20; list->S[2][1] = s21; list->S[2][2] = list->A[2][2]; 

  memcpy( list->Ap, Ap, sizeof(list->Ap) );

  list->flags &= ~(TomoimageDone|TomoimageFull);
  list->flags |= flags & (TomoimageDone|TomoimageFull);

  return E_NONE;

}
