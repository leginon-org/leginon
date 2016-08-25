/*----------------------------------------------------------------------------*
*
*  tomorefstart.c  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoref.h"
#include "exception.h"


/* functions */

extern Status TomorefStart
              (Tomoref *ref,
               Size count)

{
  Coord Ap[3][2];
  Bool full;
  Bool setmin = True, setmax = True;
  Status status;

  if ( argcheck( ref == NULL ) ) return pushexception( E_ARGVAL );

  const Tomoimage *image = ref->image;
  if ( runcheck && ( image == NULL ) ) return pushexception( E_TOMOREF );
  if ( count > image->count ) count = image->count;

  TomoimageList *list = image->list;
  if ( runcheck && ( list == NULL ) ) return pushexception( E_TOMOREF );

  const Tomoseries *series = ref->series;
  Size mincount = 0;
  Size maxcount = 0;
  Tomoflags areamatch = ref->flags & TomoflagMatch;

  for ( Size index = 0; ( index < count ) && setmin && setmax; index++ ) {

    Size min = image->min[index];
    if ( ( min < SizeMax ) && ( list[min].flags & TomoimageRef ) ) {
      status = TomometaGetTransf( series->meta, min, Ap, &full );
      if ( pushexception( status ) ) return status;
      if ( areamatch && !full ) setmin = False;
      if ( ( Ap[0][0] == 0 ) && ( Ap[0][1] == 0 ) ) setmin = False;
      if ( ( Ap[1][0] == 0 ) && ( Ap[1][1] == 0 ) ) setmin = False;
      if ( setmin ) {
        status = TomoimageSet( list + min, Ap, full );
        if ( pushexception( status ) ) return status;
        mincount = index + 1;
      }
    }

    Size max = image->max[index];
    if ( ( max < SizeMax ) && ( list[max].flags & TomoimageRef ) ) {
      status = TomometaGetTransf( series->meta, max, Ap, &full );
      if ( pushexception( status ) ) return status;
      if ( areamatch && !full ) setmax = False;
      if ( ( Ap[0][0] == 0 ) && ( Ap[0][1] == 0 ) ) setmax = False;
      if ( ( Ap[1][0] == 0 ) && ( Ap[1][1] == 0 ) ) setmax = False;
      if ( setmax ) {
        status = TomoimageSet( list + max, Ap, full );
        if ( pushexception( status ) ) return status;
        maxcount = index + 1;
      }
    }

  }

  ref->mincount = mincount;
  ref->maxcount = maxcount;

  return E_NONE;

}
