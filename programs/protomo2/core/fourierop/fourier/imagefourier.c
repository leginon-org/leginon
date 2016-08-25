/*----------------------------------------------------------------------------*
*
*  imagefourier.c  -  fourierop: image transforms
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
#include "fouriermode.h"
#include "exception.h"
#include <stdlib.h>


/* variables */

static const FourierMode ImageFourierMode[5][3][2] = {
  /*  forward call                                    backward call                                  */
  { /* 0 = asym */
    { FourierForward | FourierRealSeq,                FourierInvalid                                  },
    { FourierForward | FourierImagSeq,                FourierInvalid                                  },
    { FourierForward,                                 FourierBackward                                 },
  },
  { /* 1 = even */
    { FourierForward | FourierRealSeq | FourierEven,  FourierBackward | FourierRealSeq | FourierEven  },
    { FourierForward | FourierImagSeq | FourierEven,  FourierBackward | FourierImagSeq | FourierEven  },
    { FourierInvalid,                                 FourierInvalid                                  },
  },
  { /* 2 = odd */
    { FourierForward | FourierRealSeq | FourierOdd,   FourierBackward | FourierImagSeq | FourierOdd   },
    { FourierForward | FourierImagSeq | FourierOdd,   FourierBackward | FourierRealSeq | FourierOdd   },
    { FourierInvalid,                                 FourierInvalid                                  },
  },
  { /* 3 = herm */
    { FourierInvalid,                                 FourierInvalid                                  },
    { FourierInvalid,                                 FourierInvalid                                  },
    { FourierInvalid,                                 FourierBackward | FourierRealSeq                },
  },
  { /* 4 = antiherm */
    { FourierInvalid,                                 FourierInvalid                                  },
    { FourierInvalid,                                 FourierInvalid                                  },
    { FourierInvalid,                                 FourierBackward | FourierImagSeq                },
  },
};


static const struct {
  Type type;
  ImageAttr attr;
} ImageFourierSym[5][3] = {
  /*  output image type/attr  */
  { /* 0 = asym */
    { TypeCmplx, ImageSymHerm  },
    { TypeCmplx, ImageSymAHerm },
    { TypeCmplx, ImageAsym     },
  },
  { /* 1 = even */
    { TypeReal,  ImageSymEven  },
    { TypeImag,  ImageSymEven  },
    { TypeCmplx, ImageSymEven  },
  },
  { /* 2 = odd */
    { TypeImag,  ImageSymOdd   },
    { TypeReal,  ImageSymOdd   },
    { TypeCmplx, ImageSymOdd   },
  },
  { /* 3 = herm */
    { 0,         0             },
    { 0,         0             },
    { TypeReal,  ImageAsym     },
  },
  { /* 4 = antiherm */
    { 0,         0             },
    { 0,         0             },
    { TypeImag,  ImageAsym     },
  },
};


/* functions */

static ImageMode ImageFourierGetMode
            (Size dim,
             const Image *src)

{

  if ( !src->dim ) return 0;

  ImageMode mode = ImageModeCtr | ImageModeZero;

  if ( src->attr & ImageSymMask ) {
    if ( !src->low[0] ) {
      Bool one = False;
      for ( Size d = 1; d < dim; d++ ) {
        if ( src->len[d] <= 1 ) one = True;
        if ( src->low[d] ) mode &= ~ImageModeZero;
        if ( src->low[d] != -(Index)( src->len[d] / 2 ) ) mode &= ~ImageModeCtr;
      }
      if ( src->dim > 1 ) {
        if ( !mode ) {
          mode = ImageModeCtr | ImageModeZero;
        } else if ( mode == ( ImageModeCtr | ImageModeZero ) ) {
          if ( one ) mode = ImageModeCtr;
        }
      } else {
        mode = ImageModeCtr;
      }
    }
  } else if ( src->attr & ImageFourspc ) {
    Bool one = False;
    for ( Size d = 0; d < dim; d++ ) {
      if ( src->len[d] <= 1 ) one = True;
      if ( src->low[d] ) mode &= ~ImageModeZero;
      if ( src->low[d] != -(Index)( src->len[d] / 2 ) ) mode &= ~ImageModeCtr;
    }
    if ( !mode ) {
      mode = ImageModeCtr | ImageModeZero;
    } else if ( mode == ( ImageModeCtr | ImageModeZero ) ) {
      if ( one ) mode = ImageModeCtr;
    }
  } else {
    mode = ImageModeZero;
    for ( Size d = 0; d < dim; d++ ) {
      if ( src->low[d] ) mode &= ~ImageModeZero;
    }
  }

  return mode;

}


extern ImageFourier *ImageFourierInit
                     (const Image *src,
                      Image *dst,
                      const ImageFourierParam *param)

{
  Status status;

  /* image data type */
  Image srctmp = *src; Size type; Type seqtype = TypeUndef;
  switch ( srctmp.type ) {
    case TypeUint8:
    case TypeUint16:
    case TypeUint32:
    case TypeUint64:
    case TypeInt8:
    case TypeInt16: 
    case TypeInt32:
    case TypeInt64: seqtype = srctmp.type; srctmp.type = TypeReal; 
    case TypeReal:  type = 0; break;
    case TypeImag:  type = 1; break;
    case TypeCmplx: type = 2; break;
    default: pushexception( E_IMAGE_TYPE ); return NULL;
  }

  /* image symmetry */
  Size attr;
  switch ( srctmp.attr & ImageSymMask ) {
    case ImageAsym:     attr = 0; break;
    case ImageSymEven:  attr = 1; break;
    case ImageSymOdd:   attr = 2; break;
    case ImageSymHerm:  attr = 3; break;
    case ImageSymAHerm: attr = 4; break;
    default: pushexception( E_IMAGE_ATTR ); return NULL;
  }

  /* transform direction */
  Size back = ( src->attr & ImageFourspc ) ? 1 : 0;

  /* sequence type */
  FourierMode foumode = ImageFourierMode[attr][type][back];
  if ( foumode == FourierInvalid ) {
    pushexception( E_FOURIER_MODE ); return NULL;
  }

  /* transform dimension */
  Size maxdim = ( ( param == NULL ) || !param->maxdim ) ? src->dim : param->maxdim;
  Size seqdim = ( ( param == NULL ) || !param->seqdim ) ? SizeMax : param->seqdim;
  if ( src->dim < seqdim ) seqdim = src->dim;

  ImageMode srcmode = ImageFourierGetMode( seqdim, &srctmp );
  if ( srcmode == ( ImageModeCtr | ImageModeZero ) ) {
    pushexception( E_IMAGE_SYM ); return NULL;
  }

  /* output image */
  Image dsttmp;
  ImageMode dstmode = ImageModeFou;
  if ( param != NULL ) dstmode |= param->mode & ( ImageModeCtr | ImageModeZero );
  status = ImageMetaCopyAlloc( &srctmp, &dsttmp, dstmode );
  if ( pushexception( status ) ) return NULL;

  dstmode = ImageFourierGetMode( seqdim, &dsttmp );
  if ( dstmode == ( ImageModeCtr | ImageModeZero ) ) {
    pushexception( E_IMAGE_SYM ); goto error1;
  }
  if ( dsttmp.type != ImageFourierSym[attr][type].type ) {
    pushexception( E_IMAGEFOURIER ); goto error1;
  }
  if ( ( dsttmp.attr & ImageSymMask ) != ImageFourierSym[attr][type].attr ) {
    pushexception( E_IMAGEFOURIER ); goto error1;
  }

  /* transform options */
  FourierOpt fouopt = 0;
  if ( param != NULL ) fouopt |= param->opt & ~( FourierSymUnctr | FourierTrfUnctr );
  if ( src->attr & ImageFourspc ) {
    if ( ~srcmode & ImageModeCtr ) fouopt |= FourierTrfUnctr;
    if ( ~dstmode & ImageModeCtr ) fouopt |= FourierSymUnctr;
  } else {
    if ( ~srcmode & ImageModeCtr ) fouopt |= FourierSymUnctr;
    if ( ~dstmode & ImageModeCtr ) fouopt |= FourierTrfUnctr;
  }

  /* sequence length */
  Size *seqlen = malloc( seqdim * sizeof(*seqlen) );
  if ( seqlen == NULL ) {
    pushexception( E_MALLOC ); goto error1;
  }
  Size seqsize = 1;
  for ( Size d = 0; d < seqdim; d++ ) {
    seqlen[d] = ( src->attr & ImageFourspc ) ? dsttmp.len[d] : srctmp.len[d];
    seqsize *= seqlen[d];
  }
  Size count = 1;
  for ( Size d = seqdim; d < dsttmp.dim; d++ ) {
    dsttmp.len[d] = srctmp.len[d];
    dsttmp.low[d] = srctmp.low[d];
    if ( d < maxdim ) count *= srctmp.len[d];
  }

  /* temp buffer */
  void *cvt = NULL;
  if ( seqtype != TypeUndef ) {
    cvt = malloc( seqsize * sizeof(TypeReal) );
    if ( cvt == NULL ) {
      pushexception( E_MALLOC ); goto error2;
    }
  }

  /* create descriptor */
  ImageFourier *fou = malloc( sizeof(ImageFourier) );
  if ( fou == NULL ) {
    pushexception( E_MALLOC ); goto error3;
  }

  /* init */
  fou->fou = FourierInit( seqdim, seqlen, fouopt, foumode );
  if ( fou == NULL ) goto error4;

  fou->mode = foumode;
  fou->seqdim = seqdim;
  fou->seqlen = seqlen;
  fou->seqtype = seqtype;
  fou->cvt = cvt;
  fou->size = seqsize;
  fou->count = count;

  if ( dst == NULL ) {
    free( dsttmp.len ); free( dsttmp.low );
  } else {
    *dst = dsttmp;
  }

  return fou;


  error4: free( fou );
  error3: if ( cvt != NULL ) free( cvt );
  error2: free( seqlen );
  error1: free( dsttmp.len ); free( dsttmp.low );

  return NULL;

}


extern Status ImageFourierFinal
              (ImageFourier *fou)

{
  Status status = E_NONE;

  if ( fou != NULL ) {

    status = FourierFinal( fou->fou );

    if ( fou->cvt != NULL ) free( fou->cvt );

    free( fou->seqlen );

    free( fou );

  }

  return status;

}
