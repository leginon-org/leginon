/*----------------------------------------------------------------------------*
*
*  fourier.c  -  fourier: Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fouriercommon.h"
#include "baselib.h"
#include "message.h"
#include "coretypedefs.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* variables */

#define RegisterLength 8

static const FourierVersion *Register[RegisterLength];

static Size RegisterIndex = 0;

static Size Active[RegisterLength];

static Size ActiveIndex = 0;


/* functions */

extern Status FourierRegister
              (const FourierVersion *vers)

{

  if ( vers == NULL ) {
    return exception( E_ARGVAL );
  }

  if ( RegisterIndex >= RegisterLength ) {
    return exception( E_FOURIER );
  }

  Register[RegisterIndex++] = vers;

  return E_NONE;

}


extern Status FourierSet
              (const char *ident,
               Bool optional)

{
  Bool activated[RegisterLength];
  Status status = E_NONE;

  if ( ( ident != NULL ) && *ident ) {

    char *id = strdup( ident );
    if ( id == NULL ) return exception( E_MALLOC );

    for ( Size i = 0; i < RegisterIndex; i++ ) {
      activated[i] = False;
    }

    ActiveIndex = 0;

    char *ptr = id;  

    while ( True ) {

      char *sep = strchr( ptr, ',' );
      if ( sep != NULL ) *sep = 0;

      for ( Size i = 0; i < RegisterIndex; i++ ) {
        if ( !strcmp( ptr, Register[i]->ident ) ) {
          if ( !activated[i] ) {
            Active[ActiveIndex++] = i;
            activated[i] = True;
          }
          goto next;
        }
      }
      if ( !optional ) {
        status = exception( E_FOURIER_VERS ); goto exit;
      }

      next: if ( sep == NULL ) break;

      ptr = sep + 1;

    }

    if ( !ActiveIndex ) {
      status = exception( E_FOURIER_VERS );
    }

    exit: free( id );

  }

  return status;

}


extern char *FourierGet()

{
  Size len = 1;

  for ( Size i = 0; i < ActiveIndex; i++ ) {
    len += strlen( Register[Active[i]]->ident ) + 1;
  }

  char *fou = malloc( len );
  if ( fou == NULL ) return NULL;

  char *ptr = fou;
  for ( Size i = 0; i < ActiveIndex; i++ ) {
    const char *ident = Register[Active[i]]->ident;
    len = strlen( ident );
    memcpy( ptr, ident, len );
    ptr += len;
    *ptr++ = ',';
  }
  *ptr = 0;

  return fou;

}


static const FourierMode FourierInvSym[FourierDimSym][FourierDimSeq] = {
 /*            real         imag          complex    */
 /* asym  */ { FourierHerm, FourierAHerm, FourierAsym },
 /* even  */ { FourierEven, FourierEven,  FourierEven },
 /* odd   */ { FourierOdd,  FourierOdd,   FourierOdd  },
 /* herm  */ { FourierEven, FourierOdd,   FourierAsym },
 /* aherm */ { FourierOdd,  FourierEven,  FourierAsym }
};

static const FourierMode FourierInvType[FourierDimSym][FourierDimSeq] = {
 /*            real         imag          complex    */
 /* asym  */ { TypeCmplx,   TypeCmplx,    TypeCmplx   },
 /* even  */ { TypeReal,    TypeImag,     TypeCmplx   },
 /* odd   */ { TypeImag,    TypeReal,     TypeCmplx   },
 /* herm  */ { TypeReal,    0,            TypeReal    },
 /* aherm */ { 0,           TypeImag,     TypeImag    }
};


extern Fourier *FourierInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt,
                 FourierMode mode)

{
  Fourier *fou;
  Status status;

  if ( dim == 0 ) { pushexception( E_ARGVAL ); return NULL; }
  if ( len == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  Size sym;
  switch ( mode & FourierSymMask ) {
    case FourierAsym:  sym = 0; break;
    case FourierEven:  sym = 1; break;
    case FourierOdd:   sym = 2; break;
    case FourierHerm:  sym = 3; break;
    case FourierAHerm: sym = 4; break;
    default: pushexception( E_FOURIER_MODE ); return NULL;
  }

  Size seq, elsize;
  switch ( mode & FourierSeqMask ) {
    case FourierRealSeq:  seq = 0; elsize = sizeof(Real); break;
    case FourierImagSeq:  seq = 1; elsize = sizeof(Imag); break;
    case FourierCmplxSeq: seq = 2; elsize = sizeof(Cmplx); break;
    default: pushexception( E_FOURIER_MODE ); return NULL;
  }

  fou = malloc( sizeof( Fourier ) );
  if ( fou == NULL ) {
    pushexception( E_MALLOC ); return NULL;
  }
  fou->len = malloc( dim * sizeof( Size ) );
  if ( fou->len == NULL ) {
    pushexception( E_MALLOC ); goto error2;
  }

  Size dd = 0, seqlen = 1, foulen;
  for ( Size d = 0; d < dim; d++ ) {
    status = MulSize( seqlen, len[d], &seqlen );
    if ( status ) {
      pushexception( E_FOURIER_SIZE ); goto error1;
    }
    if ( !d || ( len[d] > 1 ) ) {
      fou->len[dd++] = len[d];
    }
  }
  if ( !seqlen ) {
    pushexception( E_FOURIER_SIZE ); goto error1;
  }

  if ( FourierInvSym[sym][seq] == FourierAsym ) {
    foulen = seqlen;
  } else {
    status = MulSize( seqlen / len[0], len[0] / 2 + 1, &foulen );
    if ( status ) {
      pushexception( E_FOURIER_SIZE ); goto error1;
    }
  }
  fou->dim = dd;
  fou->seqlen = seqlen;

  opt &= FourierOptMask;

  Size dir;
  if ( mode & FourierBackward ) {
    fou->srcsize = foulen * TypeGetSize( FourierInvType[sym][seq] );
    fou->dstsize = seqlen * elsize;
    if ( opt & FourierZeromean ) opt |= FourierSetZeromean;
    if ( ~opt & FourierTrfUnctr ) opt |= FourierDoUncenter;
    if ( sym && ( ~opt & FourierSymUnctr ) ) opt |= FourierDoCenter;
    dir = 1;
  } else {
    fou->srcsize = seqlen * elsize;
    fou->dstsize = foulen * TypeGetSize( FourierInvType[sym][seq] );
    if ( opt & FourierZeromean ) opt |= FourierSetZeroorig;
    if ( sym && ( ~opt & FourierSymUnctr ) ) opt |= FourierDoUncenter;
    if ( ~opt & FourierTrfUnctr ) opt |= FourierDoCenter;
    dir = 0;
  }

  fou->opt = opt;
  fou->mode = mode;
  fou->vers = NULL;
  fou->seq = seq;
  fou->sym = sym;
  fou->data = NULL;
  fou->tmpsize = 0;

  const FourierVersion *failvers = NULL;
  Status failstat = E_FOURIER;

  for ( Size i = 0; i < ActiveIndex; i++ ) {

    const FourierVersion *vers = Register[Active[i]];
    Status fail = E_NONE;

    if ( vers->transf[dir][fou->sym][fou->seq] == NULL ) {
      fail = E_FOURIER_IMPL;
    } else if ( vers->init != NULL ) {
      status = vers->init( fou, &fail );
      if ( exception( status ) ) goto error1;
    }
    if ( !fail ) {
      if ( fourierdebug ) {
        MessageFormat( "using %s\n", vers->ident );
      } 
      fou->vers = vers;
      return fou;
    }

    failstat = fail;
    failvers = vers;

  }

  pushexception( failstat );
  if ( failvers != NULL ) {
    appendexception( " (" );
    appendexception( failvers->ident );
    appendexception( ")" );
  }

  error1:
  free( fou->len );

  error2:
  free ( fou );

  return NULL;

}


extern Status FourierTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  const FourierVersion *vers = fou->vers;
  Size dir = ( fou->mode & FourierBackward ) ? 1 : 0;
  Status status;

  if ( ( vers == NULL ) || ( fou->seq >= FourierDimSeq ) || ( fou->sym >= FourierDimSym ) ) {
    return exception( E_FOURIER );
  }

  Status (*exec)( const Fourier *, const void *, void *, Size ) = vers->transf[dir][fou->sym][fou->seq];
  if ( exec == NULL ) {
    return exception( E_FOURIER );
  }

  status = exec( fou, src, dst, count );
  logexception( status );

  return status;

}


extern Status FourierFinal
              (Fourier *fou)

{
  Status status = E_NONE;

  if ( fou != NULL ) {

    if ( fou->vers->final != NULL ) {
      status = fou->vers->final( fou );
      logexception( status );
    }

    if ( fou->len != NULL ) free( fou->len );

    free( fou );

  }

  return status;

}


