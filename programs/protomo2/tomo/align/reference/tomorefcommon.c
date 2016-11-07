/*----------------------------------------------------------------------------*
*
*  tomorefcommon.c  -  align: reference
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
#include <string.h>


/* types */

typedef struct {
  Tomoref *ref;
  Size mincnt;
  Size maxcnt;
} TomorefArg;


/* functions */

extern void TomorefTransferParam
            (const Tomoref *ref,
             Coord A[3][3],
             Coord sampling,
             TomotransferParam *param)

{

  param->body = ref->mode.param.bck.body * sampling;
  param->bwid = ref->mode.param.bck.bwid;
  param->bthr = ref->mode.param.bck.bthr;
  param->bfsh = ( ref->mode.type == TomorefBpr ) ? TomotransferFsh( A ) : 1;

}


static Status TomorefWindowTransform
              (Size thread,
               const void *inarg,
               void *outarg)

{
  const Size *in = inarg;
  Status status;

  Size index = *in;
  Tomoref *ref = outarg;

  if ( ref->flags & TomoDryrun ) return E_NONE;

  Real *imgaddr = WindowAlloc( ref->window );
  if ( imgaddr == NULL ) return pushexception( E_MALLOC );

  TomoimageList *list = ref->image->list + index;
  const WindowFourier *fou = ref->fourier;

  status = TomoseriesResample( ref->series, ref->window, index, list->Ap, imgaddr, NULL, fou->msk );
  if ( exception( status ) ) goto exit;

  TomorefImage *refimage = ref->refimage + index;

  if ( refimage->transform == NULL ) {
    refimage->transform = WindowFourierAlloc( fou );
    if ( refimage->transform == NULL ) {
      status = pushexception( E_MALLOC ); goto exit;
    }
  }

  status = WindowTransform( fou, imgaddr, refimage->transform, NULL, NULL );
  if ( pushexception( status ) ) goto exit;

  exit: free( imgaddr );

  return status;

}


static Status TomorefWeightTransform
              (Size thread,
               const void *inarg,
               void *outarg)

{
  const Size *in = inarg;
  Status status;

  Size index = *in;
  Tomoref *ref = outarg;

  if ( ref->flags & TomoDryrun ) return E_NONE;

  status = TomorefWindowTransform( thread, inarg, outarg );
  if ( exception( status ) ) return status;

  TomoimageList *list = ref->image->list + index;
  Coord sampling = ref->series->sampling;
  const WindowFourier *win = ref->fourier;

  Coord Si[3][3];
  TomotransferScale( list->S, sampling, win->img.len, Si );

  TomorefImage *refimage = ref->refimage + index;

  Real *Hi = refimage->transfer;
  if ( Hi == NULL ) {
    Hi = malloc( win->fousize * sizeof(Real) );
    if ( Hi == NULL ) return pushexception( E_MALLOC );
    refimage->transfer = Hi;
  }

  TomotransferParam param;
  TomorefTransferParam( ref, list->A, sampling, &param );
  TomotransferCalc( win->fou.len, win->fou.low, ref->trans, ref->transcount, Si, Hi, &param );

  return E_NONE;

}


static Status TomorefWeightTransfer
              (Size thread,
               const void *inarg,
               void *outarg)

{
  const Size *in = inarg;
  TomorefArg *out = outarg;

  Size index = *in;
  Tomoref *ref = out->ref;

  if ( ref->flags & TomoDryrun ) return E_NONE;

  TomoimageList *list = ref->image->list;
  Coord sampling = ref->series->sampling;
  const WindowFourier *win = ref->fourier;

  Coord Si[3][3];
  TomotransferScale( list[index].S, sampling, win->img.len, Si );

  const TomorefImage *refimage = ref->refimage + index;
  Real *Hi = refimage->transfer;

  TomotransferParam param;
  TomorefTransferParam( ref, list[index].A, sampling, &param );

  if ( out->mincnt < SizeMax ) {
    TomotransferAdd( win->fou.len, win->fou.low, Si, list[out->mincnt].A1, Hi, &param );
  }

  if ( out->maxcnt < SizeMax ) {
    TomotransferAdd( win->fou.len, win->fou.low, Si, list[out->maxcnt].A1, Hi, &param );
  }

  return E_NONE;

}


static Status TomorefDummyTransform
              (Size thread,
               const void *inarg,
               void *outarg)

{

  return E_NONE;

}


static Bool TomorefSetThread
            (Thread *thread,
             Size *count,
             const Size *index,
             const Tomoref *ref,
             Status (*function)(Size, const void *, void *),
             void *outarg)

{
  const TomoimageList *list = ref->image->list;

  if ( ( *index < SizeMax ) && ( list[*index].flags & TomoimageRef ) && ( *index != ref->excl ) ) {
    thread[*count].function = function;
    thread[*count].inarg = index;
    thread[*count].outarg = outarg;
    (*count)++;
    return True;
  }

  return False;

}


static Thread *TomorefThreadAlloc
               (Size *count,
                Tomoref *ref,
                Status (*function)(Size, const void *, void *),
                void *outarg)

{
  const Tomoimage *image = ref->image;
  const Size *min = image->min;
  const Size *max = image->max;

  Size n = 1 + ref->mincount + ref->maxcount;
  Thread *thread = malloc( n * sizeof(Thread) );
  if ( thread == NULL ) { pushexception( E_MALLOC ); return NULL; }

  if ( ref->flags & TomoDryrun ) function = TomorefDummyTransform;

  *count = 0;

  TomorefSetThread( thread, count, &image->cooref, ref, function, outarg );

  for ( Size i = 1; i <= ref->mincount; i++, min++ ) {
    if ( TomorefSetThread( thread, count, min, ref, function, outarg ) ) {
      ref->minref = i;
    }
  }

  for ( Size i = 1; i <= ref->maxcount; i++, max++ ) {
    if ( TomorefSetThread( thread, count, max, ref, function, outarg ) ) {
      ref->maxref = i;
    }
  }

  if ( !*count ) {
    pushexception( E_TOMOREF_ZERO );
    free( thread ); thread = NULL;
  }

  return thread;

}


static void TomorefTransUpdate
            (Tomoref *ref,
             Size index)

{
  const TomoimageList *list = ref->image->list + index;
  Tomotransfer *trans = ref->trans + ref->transcount;

  memcpy( trans->A,  list->A,  sizeof(list->A) );
  memcpy( trans->A1, list->A1, sizeof(list->A1) );

  ref->transcount++;

}


static Status TomorefTransInit
              (Size count,
               Thread *thread,
               Tomoref *ref)

{

  if ( ref->trans == NULL ) {
    ref->trans = TomotransferCreate( ref->series->tilt->images );
    if ( ref->trans == NULL ) return exception( E_MALLOC );
  }
  ref->transcount = 0;

  while ( count-- ) {
    const Size *index = thread->inarg;
    TomorefTransUpdate( ref, *index );
    thread++;
  }

  return E_NONE;

}


extern Status TomorefNew
              (Tomoref *ref,
               Size exclindex)

{
  Thread *thread;
  Size count = 0;
  Status status;

  if ( argcheck( ref == NULL ) ) return pushexception( E_ARGVAL );

  if ( ref->flags & TomoLog ) {
    MessageFormat( "new reference [%"SizeU",%"SizeU"]\n", ref->mincount, ref->maxcount );
  }

  if ( runcheck && ( ref->mincount > ref->image->count ) ) return pushexception( E_TOMOREF );
  if ( runcheck && ( ref->maxcount > ref->image->count ) ) return pushexception( E_TOMOREF );

  ref->excl = exclindex;

  switch ( ref->mode.type ) {

    case TomorefSeq: {

      ref->minref = ref->mincount;
      ref->maxref = ref->maxcount;

      return E_NONE;

    }

    case TomorefMrg: {

      ref->minref = 0;
      ref->maxref = 0;

      thread = TomorefThreadAlloc( &count, ref, TomorefWindowTransform, ref );
      status = testcondition( thread == NULL );
      if ( status ) return status;

      break;

    }

    case TomorefBck:
    case TomorefBpr: {

      ref->minref = 0;
      ref->maxref = 0;

      thread = TomorefThreadAlloc( &count, ref, TomorefWeightTransform, ref );
      status = testcondition( thread == NULL );
      if ( status ) return status;

      status = TomorefTransInit( count, thread, ref );
      if ( pushexception( status ) ) goto exit;

      break;

    }

    default: return pushexception( E_TOMOREF_TYPE );

  }

  status = ThreadExec( count, thread );
  if ( status == E_THREAD_ERROR ) {
    logexception( status );
  } else if ( status ) {
    pushexception( status );
  }

  exit:

  free( thread );

  return status;

}


extern Status TomorefUpdate
              (Tomoref *ref,
               Size mincount,
               Size maxcount)

{
  Status status;

  if ( argcheck( ref == NULL ) ) return pushexception( E_ARGVAL );

  if ( mincount > ref->image->count ) mincount = ref->image->count;
  if ( maxcount > ref->image->count ) maxcount = ref->image->count;

  Size mincnt = ref->mincount;
  Size maxcnt = ref->maxcount;

  if ( runcheck && ( mincnt > mincount ) ) return pushexception( E_TOMOREF );
  if ( runcheck && ( maxcnt > maxcount ) ) return pushexception( E_TOMOREF );

  const Tomoimage *image = ref->image;
  const TomoimageList *list = image->list;
  const Size *min = image->min;
  const Size *max = image->max;

  while ( ( mincnt < mincount ) || ( maxcnt < maxcount ) ) {

    if ( ref->flags & TomoLog ) {
      MessageFormat( "increment reference [%"SizeU";%"SizeU"]\n", mincnt, maxcnt );
    }

    Size count = 0;
    Thread thread[2];
    TomorefArg arg;

    switch ( ref->mode.type ) {

      case TomorefSeq: {

        if ( mincnt < mincount ) {
          if ( ( min[mincnt] < SizeMax ) && ( list[min[mincnt]].flags & TomoimageRef ) ) {
            ref->minref = mincnt + 1;
          }
        }

        if ( maxcnt < maxcount ) {
          if ( ( max[maxcnt] < SizeMax ) && ( list[max[maxcnt]].flags & TomoimageRef ) ) {
            ref->maxref = maxcnt + 1;
          }
        }

        break;

      }

      case TomorefMrg: {

        if ( mincnt < mincount ) {
          if ( TomorefSetThread( thread, &count, min + mincnt, ref, TomorefWindowTransform, ref ) ) {
            ref->minref = mincnt + 1;
          }
        }

        if ( maxcnt < maxcount ) {
          if ( TomorefSetThread( thread, &count, max + maxcnt, ref, TomorefWindowTransform, ref ) ) {
            ref->maxref = maxcnt + 1;
          }
        }

        break;

      }

      case TomorefBck:
      case TomorefBpr: {

        arg.ref = ref;
        arg.mincnt = SizeMax;
        arg.maxcnt = SizeMax;

        if ( mincnt < mincount ) {
          if ( TomorefSetThread( thread, &count, min + mincnt, ref, TomorefWeightTransform, ref ) ) {
            TomorefTransUpdate( ref, min[mincnt] );
            arg.mincnt = mincnt;
            ref->minref = mincnt + 1;
          }
        }

        if ( maxcnt < maxcount ) {
          if ( TomorefSetThread( thread, &count, max + maxcnt, ref, TomorefWeightTransform, ref ) ) {
            TomorefTransUpdate( ref, max[maxcnt] );
            arg.maxcnt = maxcnt;
            ref->maxref = maxcnt + 1;
          }
        }

        break;

      }

      default: {
        return pushexception( E_TOMOREF_TYPE );
      }

    } /* end switch */

    if ( count ) {

      status = ThreadExec( count, thread );
      if ( status == E_THREAD_ERROR ) {
        return exception( status );
      } else if ( status ) {
        return pushexception( status );
      }

    } /* end if ( count ) */

    if ( mincnt < mincount ) ref->mincount = mincnt + 1;
    if ( maxcnt < maxcount ) ref->maxcount = maxcnt + 1;

    if ( count ) {

      switch ( ref->mode.type ) {

        case TomorefBck:
        case TomorefBpr: {

          Thread *thread = TomorefThreadAlloc( &count, ref, TomorefWeightTransfer, &arg );
          status = testcondition( thread == NULL );
          if ( status ) return status;

          status = ThreadExec( count, thread );
          if ( status == E_THREAD_ERROR ) {
            logexception( status );
          } else if ( status ) {
            pushexception( status );
          }

          free( thread );

          if ( status ) return status;

          break;

        }

        default: break;

      }

    } /* end if ( count ) */

    if ( mincnt < mincount ) mincnt++;
    if ( maxcnt < maxcount ) maxcnt++;

  } /* end while */

  return E_NONE;

}
