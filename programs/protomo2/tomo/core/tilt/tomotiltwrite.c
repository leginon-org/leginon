/*----------------------------------------------------------------------------*
*
*  tomotiltwrite.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotilt.h"
#include "exception.h"
#include "base.h"


/* constants */

#define buflen 24


/* functions */

static void TomotiltPrintInfo
            (FILE *stream,
             const char *head,
             Size number,
             const char *text1,
             const char *text)

{

  fprintf( stream, "%s%"SizeU" ", head, number );
  fputs( ( number == 1 ) ? text1 : text, stream );

}


extern Status TomotiltWrite
              (const Tomotilt *tomotilt,
               FILE *stream)

{

  if ( ( tomotilt == NULL ) || ( tomotilt->tiltstrings == NULL ) ) {
    return exception( E_ARGVAL );
  }

  /* header */
  {
    fprintf( stream, "\n TILT SERIES %s\n\n", tomotilt->tiltstrings );
    fprintf( stream, " (* file generated automagically by %s *)\n\n", Main );
    TomotiltPrintInfo( stream, " (* ", tomotilt->axes, "axis", "axes" );
    if ( tomotilt->orients != 1 ) {
      TomotiltPrintInfo( stream, ", ", tomotilt->orients, "", "groups" );
    }
    TomotiltPrintInfo( stream, " *)\n (* ", tomotilt->images, "image", "images" );
    TomotiltPrintInfo( stream, ", ", tomotilt->files, "file", "files" );
    Size cooref = tomotilt->param.cooref;
    fprintf( stream, " *)\n (* coordinate reference %"PRIu32, tomotilt->tiltimage[cooref].number );
    Size fileindex = tomotilt->tiltimage[cooref].fileindex;
    if ( fileindex < tomotilt->files ) {
      fprintf( stream, ", file %s", tomotilt->tiltstrings + tomotilt->tiltfile[fileindex].nameindex );
    }
    fprintf( stream, " *)\n" );
  }

  /* global parameters */
  {
    const TomotiltParam *param = &tomotilt->param;
    const EMparam *emparam = &param->emparam;
    if ( param->pixel > 0 ) {
      fprintf( stream, "\n\n   PARAMETER\n\n" );
      fprintf( stream, "     PIXEL SIZE %-.10"CoordG" nm\n", param->pixel * 1e9 );
    }
    if ( ( emparam->cs > 0 ) || ( emparam->lambda > 0 ) ) {
      fprintf( stream, "\n\n   PARAMETER\n\n" );
      if ( emparam->lambda > 0 ) {
        fprintf( stream, "     WAVELENGTH %-.10"CoordG" nm\n", emparam->lambda * 1e9 );
      }
      if ( emparam->cs > 0 ) {
        fprintf( stream, "     SPHERICAL ABERRATION %-.10"CoordG" mm\n", emparam->cs * 1e3 );
      }
      if ( emparam->beta > 0 ) {
        fprintf( stream, "     ILLUMINATION DIVERGENCE %8.3"CoordF" mrad\n", emparam->beta * 1e3 );
      }
      if ( emparam->fs > 0 ) {
        fprintf( stream, "     FOCUS SPREAD %8.3"CoordF" nm\n", emparam->fs * 1e9 );
      }
    }
    if ( ( param->euler[0] != 0 ) || ( param->euler[1] != 0 ) || ( param->euler[2] != 0 ) ) {
      fprintf( stream, "\n\n   PARAMETER\n\n" );
      if ( param->euler[0] != 0 ) {
        fprintf( stream, "     PSI   %- 8.3"CoordF"\n", param->euler[0] );
      }
      if ( param->euler[1] != 0 ) {
        fprintf( stream, "     THETA %- 8.3"CoordF"\n", param->euler[1] );
      }
      if ( param->euler[2] != 0 ) {
        fprintf( stream, "     PHI   %- 8.3"CoordF"\n", param->euler[2] );
      }
    }
    if ( ( param->origin[0] != 0 ) || ( param->origin[1] != 0 ) || ( param->origin[2] != 0 ) ) {
      fprintf( stream, "\n\n   PARAMETER\n\n" );
      fprintf( stream, "     ORIGIN  [ %.3"CoordF" %.3"CoordF" %.3"CoordF" ]\n", param->origin[0], param->origin[1], param->origin[2] );
    }
  }

  for ( Size axis = 0; axis < tomotilt->axes; axis++) {

    TomotiltAxis *tiltaxis = tomotilt->tiltaxis + axis;

    fprintf( stream, "\n\n   AXIS\n\n" );
    fprintf( stream, "     TILT AZIMUTH   %- 8.3"CoordF"\n", tiltaxis->phi );
    if ( tiltaxis->theta != 0 ) {
      fprintf( stream, "     TILT ELEVATION %- 8.3"CoordF"\n", tiltaxis->theta );
    }
    if ( tiltaxis->offset != 0 ) {
      fprintf( stream, "     TILT OFFSET    %- 8.3"CoordF"\n", tiltaxis->offset );
    }

    for ( Size orient = 0; orient < tomotilt->orients; orient++ ) {

      TomotiltOrient *tiltorient = tomotilt->tiltorient + orient;
      Bool flag = False, ref = False;

      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          if ( image == tiltaxis->cooref ) ref = True;
          flag = True;
        }
      }
      if ( !flag ) continue;

      if ( ( tiltorient->euler[0] != 0 ) || ( tiltorient->euler[1] != 0 ) || ( tiltorient->euler[2] != 0 ) || orient ) {
        fprintf( stream, "\n\n   ORIENTATION\n\n" );
        if ( tiltorient->euler[0] != 0 ) {
          fprintf( stream, "     PSI   %- 8.3"CoordF"\n", tiltorient->euler[0] );
        }
        if ( tiltorient->euler[1] != 0 ) {
          fprintf( stream, "     THETA %- 8.3"CoordF"\n", tiltorient->euler[1] );
        }
        if ( ( tiltorient->euler[2] != 0 ) || orient ) {
          fprintf( stream, "     PHI   %- 8.3"CoordF"\n", tiltorient->euler[2] );
        }
      }

      flag = False;
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          Size fileindex = img->fileindex;
          if ( fileindex < tomotilt->files ) {
            TomotiltFile *file = tomotilt->tiltfile + fileindex;
            Size nameindex = file->nameindex;
            if ( !flag ) fprintf( stream, "\n" ); flag = True;
            fprintf( stream, "   IMAGE %-4"PRIu32"  FILE %s", img->number, tomotilt->tiltstrings + nameindex );
            if ( file->dim > 2 ) {
              fprintf( stream, "[%"PRId64"]", img->fileoffset );
            }
            fprintf( stream, "\n" );
          }
        }
      }

      fprintf( stream, "\n" );
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          fprintf( stream, "   IMAGE %-4"PRIu32"  ORIGIN  [% 9.3"CoordF" % 9.3"CoordF" ]\n", img->number, geom->origin[0], geom->origin[1] );
        }
      }

      fprintf( stream, "\n" );
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          fprintf( stream, "   IMAGE %-4"PRIu32"  TILT ANGLE %8.3"CoordF"    ROTATION %8.3"CoordF"\n", img->number, geom->theta, geom->alpha );
        }
      }

      flag = False;
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          if ( geom->scale > 0 ) {
            if ( !flag ) fprintf( stream, "\n" ); flag = True;
            fprintf( stream, "   IMAGE %-4"PRIu32"  SCALE  %8.6"CoordF"\n", img->number, geom->scale );
          }
        }
      }

      flag = False;
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          if ( geom->corr[0] > 0 ) {
            if ( !flag ) fprintf( stream, "\n" ); flag = True;
            fprintf( stream, "   IMAGE %-4"PRIu32"  CORRECTION  %8.6"CoordF"  %8.6"CoordF"  %8.3"CoordF"\n", img->number, geom->corr[0], geom->corr[1], geom->beta );
          }
        }
      }

      flag = False;
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          if ( img->defocus < TomotiltValMax ) {
            if ( !flag ) fprintf( stream, "\n" ); flag = True;
            fprintf( stream, "   IMAGE %-4"PRIu32"  DEFOCUS  %-.10"CoordG" nm   [% 9.3"CoordF" % 9.3"CoordF" ]\n", img->number, img->defocus * 1e9, img->loc[0], img->loc[1] );
          }
        }
      }

      flag = False;
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          if ( img->ca > 0 ) {
            if ( !flag ) fprintf( stream, "\n" ); flag = True;
            fprintf( stream, "   IMAGE %-4"PRIu32"  ASTIGMATISM  %8.6"CoordF"  %8.3"CoordF"\n", img->number, img->ca, img->phia );
          }
        }
      }

      flag = False;
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          if ( img->ampcon != 0 ) {
            if ( !flag ) fprintf( stream, "\n" ); flag = True;
            fprintf( stream, "   IMAGE %-4"PRIu32"  AMPLITUDE CONTRAST %8.3"CoordF"\n", img->number, img->ampcon );
          }
        }
      }

      flag = False;
      for ( Size image = 0; image < tomotilt->images; image++ ) {
        TomotiltGeom *geom = tomotilt->tiltgeom + image;
        if ( ( geom->axisindex == axis ) && ( geom->orientindex == orient ) ) {
          TomotiltImage *img = tomotilt->tiltimage + image;
          if ( img->pixel > 0 ) {
            if ( !flag ) fprintf( stream, "\n" ); flag = True;
            fprintf( stream, "   IMAGE %-4"PRIu32"  PIXEL SIZE %-.10"CoordG" nm\n", img->number, img->pixel * 1e9 );
          }
        }
      }

      if ( ref ) {
        TomotiltImage *img = tomotilt->tiltimage + tiltaxis->cooref;
        fprintf( stream, "\n   REFERENCE IMAGE %-4"PRIu32"\n", img->number );
      }

    } /* end for orient */

  } /* end for axis */

  fprintf( stream, "\n\n END\n\n" );

  return E_NONE;

}
