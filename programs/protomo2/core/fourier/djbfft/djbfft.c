/*----------------------------------------------------------------------------*
*
*  djbfft.c  -  djbfft: fast Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "djbfftcommon.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* functions */

static void DJBfftCleanup
            (Size dim,
             DJBfftData *data)

{

  while ( dim-- ) {
    if ( data->rtab != NULL ) free( data->rtab );
    if ( data->ctab != NULL ) free( data->ctab );
    if ( data->tmp  != NULL ) free( data->tmp );
    data++;
  }

}


extern Status DJBfftInit
              (Fourier *fou,
               Status *stat)

{
  Status status = E_NONE;

  if ( sizeof(Real32) != sizeof(Real) ) {
    return exception( E_DJBFFT );
  }

  if ( !fou->dim ) {
    return exception( E_ARGVAL );
  }

  DJBfftData *data = malloc( fou->dim * sizeof(DJBfftData) );
  if ( data == NULL ) return exception( E_MALLOC );

  for ( Size d = 0; d < fou->dim; d++ ) {
    DJBfftData *t = data + d;
    t->rtab = NULL;
    t->ctab = NULL;
    t->tmp = NULL;
    t->scale = 1.0;
  }

  Size ntmp = 0;
  for ( Size d = 0; d < fou->dim; d++ ) {
    Size len = fou->len[d];
    DJBfftData *t = data + d;
    switch ( len ) {
      case    2: t->fr = fftr4_2;    t->br = fftr4_un2;    t->fc = fftc4_2;    t->bc = fftc4_un2;    break;
      case    4: t->fr = fftr4_4;    t->br = fftr4_un4;    t->fc = fftc4_4;    t->bc = fftc4_un4;    break;
      case    8: t->fr = fftr4_8;    t->br = fftr4_un8;    t->fc = fftc4_8;    t->bc = fftc4_un8;    break;
      case   16: t->fr = fftr4_16;   t->br = fftr4_un16;   t->fc = fftc4_16;   t->bc = fftc4_un16;   break;
      case   32: t->fr = fftr4_32;   t->br = fftr4_un32;   t->fc = fftc4_32;   t->bc = fftc4_un32;   break;
      case   64: t->fr = fftr4_64;   t->br = fftr4_un64;   t->fc = fftc4_64;   t->bc = fftc4_un64;   break;
      case  128: t->fr = fftr4_128;  t->br = fftr4_un128;  t->fc = fftc4_128;  t->bc = fftc4_un128;  break;
      case  256: t->fr = fftr4_256;  t->br = fftr4_un256;  t->fc = fftc4_256;  t->bc = fftc4_un256;  break;
      case  512: t->fr = fftr4_512;  t->br = fftr4_un512;  t->fc = fftc4_512;  t->bc = fftc4_un512;  break;
      case 1024: t->fr = fftr4_1024; t->br = fftr4_un1024; t->fc = fftc4_1024; t->bc = fftc4_un1024; break;
      case 2048: t->fr = fftr4_2048; t->br = fftr4_un2048; t->fc = fftc4_2048; t->bc = fftc4_un2048; break;
      case 4096: t->fr = fftr4_4096; t->br = fftr4_un4096; t->fc = fftc4_4096; t->bc = fftc4_un4096; break;
      case 8192: t->fr = fftr4_8192; t->br = fftr4_un8192; t->fc = fftc4_8192; t->bc = fftc4_un8192; break;
      default: *stat = exception( E_DJBFFT_SIZE ); goto error;
    }
    if ( fou->mode & FourierSeqMask ) {
      t->rtab = malloc( len * sizeof(*t->rtab) );
      if ( t->rtab == NULL ) goto error;
      fftfreq_rtable( t->rtab, len );
      for ( Size i = 0; i < len; i++ ) {
        if ( t->rtab[i] >= len ) goto fail;
        t->rtab[i] = t->rtab[i] ? len - t->rtab[i] : 0;
      }
    }
    if ( d || !( fou->mode & FourierSeqMask ) ) {
      t->ctab = malloc( len * sizeof(*t->ctab) );
      if ( t->ctab == NULL ) goto error;
      fftfreq_ctable( t->ctab, len );
      for ( Size i = 0; i < len; i++ ) {
        if ( t->ctab[i] >= len ) goto fail;
        t->ctab[i] = t->ctab[i] ? len - t->ctab[i] : 0;
      }
    }
    Size nt = len;
    if ( fou->mode & FourierSeqMask ) {
      if ( fou->mode & FourierBackward ) {
        nt = d ? 2 * len : len / 2 + 1;
      } else {
        nt = d ? len : len / 2 + 1;
      }
    }
    if ( nt > ntmp ) ntmp = nt;
  }
  fou->tmpsize = ntmp * sizeof(Cmplx);
  if ( ntmp ) {
    data[0].tmp = malloc( fou->tmpsize );
    if ( data[0].tmp == NULL ) goto error;
  }

  if ( fou->opt & FourierUnscaled ) {
    if ( fou->mode & FourierBackward ) {
      data[0].scale /= fou->seqlen;
    }
  } else {
    if ( ~fou->mode & FourierBackward ) {
      data[0].scale /= fou->seqlen;
    }
  }

  fou->data = data;
  *stat = E_NONE;
  return E_NONE;

  fail:
  status = exception( E_DJBFFT );

  error:
  DJBfftCleanup( fou->dim, data );
  free( data );

  return status;

}


extern Status DJBfftFinal
              (Fourier *fou)

{

  if ( fou != NULL ) {

    if ( fou->data != NULL ) {
      DJBfftCleanup( fou->dim, fou->data );
      free( fou->data );
      fou->data = NULL;
    }

  }

  return E_NONE;

}
