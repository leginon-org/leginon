/*----------------------------------------------------------------------------*
*
*  tomoreftransform.c  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomorefcommon.h"
#include "imagearray.h"
#include "imagemask.h"
#include "imageio.h"
#include "message.h"
#include "thread.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Cmplx *TomorefTransform
              (const Tomoref *ref,
               const Size *refsort,
               Size refindex,
               const Size *imgsort,
               Size imgindex)

{
  Size index;
  Status status;

  if ( argcheck( ref  == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( imgsort == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  const WindowFourier *fou = ref->fourier;
  Cmplx *refaddr = WindowFourierAlloc( fou );
  if ( refaddr == NULL ) { pushexception( E_MALLOC ); return NULL; }

  TomorefType reftype = ref->mode.type;
  if ( !ref->minref && !ref->maxref ) {
    reftype = TomorefSeq;
  }

  const Tomoimage *image = ref->image;
  TomoimageList *list = image->list;
  Size images = ref->series->tilt->images;

  switch ( reftype ) {

    case TomorefSeq: {

      index = ( refsort == NULL ) ? image->cooref : refsort[refindex];
      if ( index >= images ) { status = pushexception( E_TOMOREF ); goto error; }

      if ( ref->flags & TomoLog ) {
        MessageFormat( "reference transform %"SizeU", image %"SizeU"\n", index, imgsort[imgindex] );
      }

      const Window *img = ref->window;
      Real *imgaddr = WindowAlloc( img );
      if ( imgaddr == NULL ) { status = pushexception( E_MALLOC ); goto error; }

      status = TomoseriesResample( ref->series, img, index, list[index].Ap, imgaddr, NULL, fou->msk );
      if ( exception( status ) ) goto exitseq;

      status = FourierRealTransf( fou->forw, imgaddr, refaddr, 1 );
      if ( pushexception( status ) ) goto exitseq;

      exitseq: free( imgaddr );

      break;

    }

    case TomorefMrg: {

      index = ( imgindex == SizeMax ) ? image->cooref : imgsort[imgindex];
      if ( index >= images ) { status = pushexception( E_TOMOREF ); goto error; }

      if ( ref->flags & TomoLog ) {
        MessageFormat( "merged reference transform, image %"SizeU"\n", index );
      }

      Coord *n = malloc( fou->fousize * sizeof(Coord) );
      if ( n == NULL ) { status = pushexception( E_MALLOC ); goto error; }

      status = TomorefMrgTransform( ref, index, refaddr, n, ref->mode.param.mrg.dz );
      logexception( status );

      free( n );

      break;

    }

    case TomorefBck:
    case TomorefBpr: {

      index = ( imgindex == SizeMax ) ? image->cooref : imgsort[imgindex];
      if ( index >= images ) { status = pushexception( E_TOMOREF ); goto error; }

      if ( ref->flags & TomoLog ) {
        MessageFormat( "backprojection reference transform, image %"SizeU"\n", index );
      }

      Real *sncaddr = malloc( fou->fousize * sizeof(Real) );
      if ( sncaddr == NULL ) { status = pushexception( E_MALLOC ); goto error; }

      TomotransferParam param;
      TomorefTransferParam( ref, list[index].A, ref->series->sampling, &param );

      status = TomorefBckTransform( ref, index, refaddr, sncaddr, &param );
      logexception( status );

      free( sncaddr );

      break;

    }

    default: status = pushexception( E_TOMOREF_TYPE );

  }

  if ( status ) goto error;

  status = CCFmodCmplx( fou->fousize, refaddr, fou->mode );
  if ( pushexception( status ) ) goto error;

  if ( fou->flt != NULL ) {

    status = ImageMask( &fou->fou, refaddr, (void *)list[index].Af, NULL, fou->flt );
    if ( pushexception( status ) ) goto error;

  }

  return refaddr;

  error: free( refaddr );

  return NULL;

}
