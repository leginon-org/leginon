/*----------------------------------------------------------------------------*
*
*  protomo.c  -  python tomography extension
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "protomomodule.h"
#include "tomopyimage.h"


/* variables */

TomoPy *protomo = NULL;


/* functions */

extern PyMODINIT_FUNC initprotomo()

{

  protomo = TomoPyInit( ProtomoName );

  ModuleInitAfter( &ProtomoModule );

  TomoPyImageInit( protomo );

  ProtomoParamInit( protomo );

  ProtomoGeomInit( protomo );

  ProtomoSeriesInit( protomo );

}
