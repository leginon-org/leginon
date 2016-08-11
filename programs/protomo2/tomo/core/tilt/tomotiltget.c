/*----------------------------------------------------------------------------*
*
*  tomotiltget.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotilt.h"
#include "exception.h"


/* functions */

extern uint32_t TomotiltGetIndex
                (const Tomotilt *tomotilt,
                 Size number)

{

  if ( tomotilt == NULL ) return TomotiltImageMax;

  for ( Size index = 0; index < tomotilt->images; index++ ) {
    if ( tomotilt->tiltimage[index].number == number ) {
      return index;
    }
  }

  return TomotiltImageMax;

}
