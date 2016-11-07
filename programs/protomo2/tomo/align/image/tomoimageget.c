/*----------------------------------------------------------------------------*
*
*  tomoimageget.c  -  align: image geometry
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
#include "exception.h"


/* functions */

extern Status TomoimageGet
              (const Tomoseries *series,
               TomoimageList *list,
               Size index,
               Bool fulltransf)

{
  Coord Ap[3][2];
  Coord (*Bp)[2] = Ap;
  TomoimageFlags flags = 0;
  Bool full;
  Status status;

  Tomogeom *geom = series->geom + index;

  status = TomometaGetTransf( series->meta, index, Ap, &full );
  if ( exception( status ) ) return status;

  if ( ( ( Ap[0][0] == 0 ) && ( Ap[0][1] == 0 ) ) || ( ( Ap[1][0] == 0 ) && ( Ap[1][1] == 0 ) ) ) {

    if ( fulltransf ) {
      Bp = geom->Aa;
      if ( ( ( Bp[0][0] == 0 ) && ( Bp[0][1] == 0 ) ) || ( ( Bp[1][0] == 0 ) && ( Bp[1][1] == 0 ) ) ) {
        Bp = geom->Ap;
      } else {
        flags = TomoimageFull;
      }
    } else {
      Bp = geom->Ap;
    }

  } else {

    if ( fulltransf ) {
      if ( full ) {
        flags = TomoimageDone | TomoimageFull;
      }
    } else {
      if ( full ) {
        Bp = geom->Ap;
      } else {
        flags = TomoimageDone;
      }
    }

  }

  status = TomoimageSet( list + index, Bp, flags );
  if ( exception( status ) ) return status;

  return E_NONE;

}
