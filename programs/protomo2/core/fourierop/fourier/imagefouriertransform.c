/*----------------------------------------------------------------------------*
*
*  imagefouriertransform.c  -  fourierop: image transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagefouriercommon.h"
#include "transfer.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */


extern Status ImageFourierTransf
              (const ImageFourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  Status status;

  if ( fou->seqtype != TypeUndef ) {
    status = ScaleReal( fou->seqtype, fou->size, src, fou->cvt, NULL );
    if ( exception( status ) ) return status;
    src = fou->cvt;
  }

  status = FourierTransf( fou->fou, src, dst, count * fou->count );

  return status;

}


extern Status ImageFourierTransform
              (const Image *srcimg,
               const void *src,
               Image *dstimg,
               void *dst,
               Size count,
               const ImageFourierParam *param)

{
  Status stat, status;

  ImageFourier *fou = ImageFourierInit( srcimg, dstimg, param );
  status = testcondition( fou == NULL );
  if ( status ) return status;

  status = ImageFourierTransf( fou, src, dst, count );
  pushexception( status );

  stat = ImageFourierFinal( fou );
  if ( !status ) if ( pushexception( stat ) ) status = stat;

  return status;

}
