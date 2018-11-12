/*----------------------------------------------------------------------------*
*
*  tomorefcommon.h  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomorefcommon_h_
#define tomorefcommon_h_

#include "tomoref.h"


/* prototypes */

extern void TomorefTransferParam
            (const Tomoref *ref,
             Coord A[3][3],
             Coord sampling,
             TomotransferParam *param);

extern Status TomorefMrgTransform
              (const Tomoref *ref,
               Size index,
               Cmplx *addr,
               Coord *n,
               Coord dz);

extern Status TomorefBckTransform
              (const Tomoref *ref,
               Size index,
               Cmplx *addr,
               Real *sinc,
               const TomotransferParam *param);


#endif
