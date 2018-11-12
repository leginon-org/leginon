/*----------------------------------------------------------------------------*
*
*  imagectfprint.c  -  image: contrast transfer function
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
#include "message.h"
#include "exception.h"


/* functions */

extern Status ImageCTFPrintParam
              (const EMparam *empar,
               const ImageCTFParam *param)

{

  if ( argcheck( param == NULL ) ) return exception( E_ARGVAL );

  MessageFormatBegin( "%.6"CoordG" nm/pixel\n", param->pixel * 1e9 );
  MessageFormatPrint( "dz = %.6"CoordG" nm\n", param->dz * 1e9 );
  if ( param->ampcon != 0 ) {
    MessageFormatPrint( "amplitude contrast phase = %.3"CoordF" degrees\n", param->ampcon );
  }
  if ( param->ca > 0 ) {
    Coord dzmin = param->dz * ( 1 - param->ca / 2 );
    Coord dzmax = param->dz * ( 1 + param->ca / 2 );
    MessageFormatPrint( "axial astigm = %.6"CoordG"  %.6"CoordG" degrees\n", param->ca, param->phia );
    MessageFormatPrint( "dzmin, dzmax = %.6"CoordG" nm  %.6"CoordG" nm\n", dzmin, dzmax );
  }
  if ( empar != NULL ) {
    MessageFormatPrint( "U = %.6"CoordG" kV    lambda = %.6"CoordG" nm\n", LAMBDA_TO_U( empar->lambda ) * 1e-3, empar->lambda * 1e9 );
    MessageFormatPrint( "Cs = %.6"CoordG" mm\n", empar->cs * 1e3 );
    if ( empar->beta > 0 ) {
      MessageFormatPrint( "%s: illum.diverg = %.6"CoordG" mrad\n", empar->beta * 1e3 );
    }
    if ( empar->fs > 0 ) {
      MessageFormatPrint( "%s: focus spread = %.6"CoordG" nm\n", empar->fs * 1e9 );
    }
  }
  MessageFormatEnd( NULL );

  return E_NONE;

}
