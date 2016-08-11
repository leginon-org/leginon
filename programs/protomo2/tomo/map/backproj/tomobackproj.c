/*----------------------------------------------------------------------------*
*
*  tomobackproj.c  -  map: weighted backprojection
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomobackproj.h"
#include "tomomapcommon.h"
#include "exception.h"


/* functions */

extern Status TomobackprojInit
              (Tomomap *map)

{
  Status status;

  map->data.trans = TomotransferCreate( map->count );
  status = testcondition( map->data.trans == NULL );

  return status;

}


extern Status TomobackprojFinal
              (Tomomap *map)

{
  Status status;

  status = TomotransferDestroy( map->count, map->data.trans );
  logexception( status );

  map->data.trans = NULL;

  return status;

}


extern Tomotransfer *TomobackprojGetTransfer
                     (Tomomap *map)

{

  if ( map == NULL ) return NULL;

  return map->data.trans;

}
