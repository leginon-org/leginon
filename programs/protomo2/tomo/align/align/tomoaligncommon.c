/*----------------------------------------------------------------------------*
*
*  tomoaligncommon.c  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoaligncommon.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>


/* functions */

extern Status TomoalignCorrWrite
              (Tomodiagn *diagn,
               const Size index,
               const Size *srclen,
               const void *srcaddr,
               const Size *dstlen,
               Real *dstaddr,
               Real norm)

{
  Size ori[2];
  Status status;

  ori[0] = srclen[0] - dstlen[0] / 2;
  ori[1] = srclen[1] - dstlen[1] / 2;

  status = ArrayCutCyc( 2, srclen, srcaddr, ori, dstlen, dstaddr, sizeof(Real) );
  if ( pushexception( status ) ) return status;

  if ( norm > 0 ) {
    for ( Size i = 0; i < dstlen[0] * dstlen[1]; i++ ) {
      dstaddr[i] /= norm;
    }
  }

  status = TomodiagnWrite( diagn, index, dstaddr );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern void TomoalignDryrunLog
            (const Tomoalign *align,
             Size index)

{
  const TomoimageList *list = align->image->list + index;
  const Tomodata *data = align->series->data;
  const Tomotilt *tilt = align->series->tilt;
  const TomotiltGeom *geom = tilt->tiltgeom + index;
  const TomotiltAxis *axis = tilt->tiltaxis + geom->axisindex;

  char logbuf[TomoalignLogbuflen];
  TomodataLogString( data, data->dscr, index, logbuf, TomoalignLogbuflen );

  char alistat[] = ".....";
  if ( list->flags & TomoimageSel  ) alistat[0] = 'S';
  if ( list->flags & TomoimageRef  ) alistat[1] = 'R';
  if ( list->flags & TomoimageAli  ) alistat[2] = 'A';
  if ( list->flags & TomoimageDone ) alistat[3] = 'D'; 
  if ( list->flags & TomoimageFull ) alistat[4] = 'F'; 

  MessageFormat( "%s   %s   %"PRIu32": %-8.3f   %7.3f\n", logbuf, alistat, geom->axisindex, axis->phi, geom->theta );

}


