/*----------------------------------------------------------------------------*
*
*  imagectfcmplx.c  -  image: contrast transfer function
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagectf.h"
#include "exception.h"


/* functions */

extern Status ImageCTFCmplx
              (const Image *image,
               void *addr,
               const EMparam *empar,
               const ImageCTFParam *param)

{

  if ( argcheck( image == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( empar == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( ~image->attr & ImageFourspc ) ) return exception( E_IMAGECTF );

  if ( image->dim != 2 ) return exception( E_IMAGECTF_DIM );

  Coord lambda = empar->lambda, lambda2 = lambda * lambda;
  Coord cs = empar->cs;
  Coord beta = ( empar->beta > 0 ) ? empar->beta : 0;
  Coord fs2 = ( empar->fs > 0 ) ? ( empar->fs * empar->fs ) : 0;

  Coord pixel = param->pixel;
  Coord dz = param->dz;
  Coord ca = ( param->ca > 0 ) ? param->ca / 2 : 0;
  Coord phia = param->phia * Pi / 180;
  Coord ampcon = param->ampcon * Pi / 180;

  Size nx = image->len[0];
  Size ny = image->len[1];

  Size sx;
  if ( image->attr & ImageSymMask ) {
    sx = 2 * ( nx - 1 ); if ( image->attr & ImageNodd ) sx++;
  } else {
    sx = nx;
  }

  Coord x0 = ( image->low == NULL ) ? -(Coord)( sx / 2 ) : image->low[0];
  Coord y0 = ( image->low == NULL ) ? -(Coord)( ny / 2 ) : image->low[1];

  Cmplx *d = addr;

  for ( Size iy = 0; iy < ny; iy++ ) {

    Coord y = ( iy + y0 ) / ( pixel * ny ), y2 = y * y;

    for ( Size ix = 0; ix < nx; ix++ ) {

      Coord x = ( ix + x0 ) / ( pixel * sx ), x2 = x * x;

      Coord re;

      if ( ca > 0 ) {

        Coord k2 = x2 + y2;
        Coord phik = atan2( y, x );
        Coord dzk = dz * ( 1 - ca * Cos( 2 * ( phik - phia ) ) );
        Coord gamma = Pi * lambda * k2 * ( cs * lambda2 * k2 / 2 + dzk );
        if ( ( beta > 0 ) || ( fs2 > 0 ) ) {
          Coord b = beta * ( cs * lambda2 * k2 - dzk );
          Coord E = Exp( -Pi * Pi * k2 * ( fs2 * lambda2 * k2 / 2 + 2 * b * b ) );
          re = -E * Sin( gamma + ampcon );
        } else {
          re = -Sin( gamma + ampcon );
        }

      } else {

        Coord k2 = x2 + y2;
        Coord gamma = Pi * lambda * k2 * ( cs * lambda2 * k2 / 2 + dz );
        if ( ( beta > 0 ) || ( fs2 > 0 ) ) {
          Coord b = beta * ( cs * lambda2 * k2 - dz );
          Coord E = exp( -Pi * Pi * k2 * ( fs2 * lambda2 * k2 / 2 + 2 * b * b ) );
          re = -E * Sin( gamma + ampcon );
        } else {
          re = -Sin( gamma + ampcon );
        }

      }

      Cset( *d++, re, 0 );

    } /* end for ix */

  } /* end for iy */

  return E_NONE;

}
