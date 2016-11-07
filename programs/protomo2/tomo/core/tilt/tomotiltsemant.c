/*----------------------------------------------------------------------------*
*
*  tomotiltsemant.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotiltsemant.h"
#include "tomotiltnew.h"
#include "stringparse.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* macros */

#define TomotiltParseCheckArg( expr )  ( ( expr ) ? pushexception( E_TOMOTILT ) : E_NONE )

#define TomotiltParseCheck( expr )  ( ( expr ) ? ( tiltparse->parse->status = pushexception( E_TOMOTILT ) ) : E_NONE )


/* functions */

extern Size TomotiltParseToUint
            (TomotiltParse *tiltparse,
             ParseSymb *symb)

{
  Size var;

  if ( StringParseSize( symb->txt, NULL, &var, NULL ) ) {
    ParseError( tiltparse->parse, &symb->loc, exception( E_TOMOTILT_INT ) );
    var = SizeMax;
  }

  return var;

}


extern Index TomotiltParseToInt
             (TomotiltParse *tiltparse,
              ParseSymb *symb)

{
  Index var;

  if ( StringParseIndex( symb->txt, NULL, &var, NULL ) ) {
    ParseError( tiltparse->parse, &symb->loc, exception( E_TOMOTILT_INT ) );
    var = IndexMax;
  }

  return var;

}


extern Coord TomotiltParseToReal
             (TomotiltParse *tiltparse,
              ParseSymb *symb)

{
  Coord var;

  if ( StringParseCoord( symb->txt, NULL, &var, NULL ) ) {
    ParseError( tiltparse->parse, &symb->loc, exception( E_TOMOTILT_REAL ) );
    var = CoordMax;
  }

  return var;

}


extern void TomotiltParseStoreParam
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             Coord *val)

{

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return;

  if ( tiltparse->state != STATE_PARAM ) {
    ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_DEF ) );
  }

  if ( tiltparse->parse->status ) return;

  switch ( type ) {
    case FIELD_PSI0: {
      if ( tomotilt->param.euler[0] != CoordMax ) goto redef;
      tomotilt->param.euler[0] = *val;
      return;
    }
    case FIELD_THE0: {
      if ( tomotilt->param.euler[1] != CoordMax ) goto redef;
      tomotilt->param.euler[1] = *val;
      return;
    }
    case FIELD_PHI0: {
      if ( tomotilt->param.euler[2] != CoordMax ) goto redef;
      tomotilt->param.euler[2] = *val;
      return;
    }
    case FIELD_ORI0: {
      if ( tomotilt->param.origin[0] != CoordMax ) goto redef;
      if ( tomotilt->param.origin[1] != CoordMax ) goto redef;
      if ( tomotilt->param.origin[2] != CoordMax ) goto redef;
      tomotilt->param.origin[0] = val[0];
      tomotilt->param.origin[1] = val[1];
      tomotilt->param.origin[2] = val[2];
      return;
    }
    case FIELD_CS: {
      if ( tomotilt->param.emparam.cs > 0 ) goto redef;
      if ( *val <= 0 ) goto value;
      tomotilt->param.emparam.cs = *val;
      return;
    }
    case FIELD_HT: {
      if ( tomotilt->param.emparam.lambda > 0 ) goto redef;
      if ( *val <= 0 ) goto value;
      tomotilt->param.emparam.lambda = LAMBDA( *val );
      return;
    }
    case FIELD_LAMBDA: {
      if ( tomotilt->param.emparam.lambda > 0 ) goto redef;
      if ( *val <= 0 ) goto value;
      tomotilt->param.emparam.lambda = *val;
      return;
    }
    case FIELD_BETA: {
      if ( tomotilt->param.emparam.beta > 0 ) goto redef;
      tomotilt->param.emparam.beta = *val;
      return;
    }
    case FIELD_FS: {
      if ( tomotilt->param.emparam.fs > 0 ) goto redef;
      tomotilt->param.emparam.fs = *val;
      return;
    }
    case FIELD_PIXEL0: {
      if ( tomotilt->param.pixel > 0 ) goto redef;
      if ( *val <= 0 ) goto value;
      tomotilt->param.pixel = *val;
      return;
    }
  }
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT ) );
  return;

  redef:
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_DEF ) );
  return;

  value:
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_VAL ) );
  return;

}


extern void TomotiltParseStoreAxis
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             Coord val)

{
  TomotiltAxis *axis;
  Size index, index2;
  Status status;

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return;

  if ( tiltparse->parse->status ) return;

  tiltparse->imageindex = TomotiltImageMax;

  if ( tiltparse->state & STATE_AXIS ) {
    index = tiltparse->axisindex;
    TomotiltParseCheck( index >= tomotilt->axes );
  } else {
    status = TomotiltNewAxis( tomotilt, &index );
    if ( status ) {
      ParseError( tiltparse->parse, &err->loc, exception( status ) );
    } else {
      tiltparse->axisindex = index;
      status = TomotiltNewOrient( tomotilt, index, &index2 );
      if ( status ) {
        ParseError( tiltparse->parse, &err->loc, exception( status ) );
      } else {
        tiltparse->orientindex = index2;
      }
      tiltparse->state = STATE_AXIS | STATE_ORIENT;
    }
  }

  if ( tiltparse->parse->status ) return;

  axis = tomotilt->tiltaxis;
  if ( TomotiltParseCheck( axis == NULL ) ) return;
  axis += index;

  switch ( type ) {
    case FIELD_AZIM: {
      if ( axis->phi != CoordMax ) goto redef;
      axis->phi = val;
      return;
    }
    case FIELD_ELEV: {
      if ( axis->theta != CoordMax ) goto redef;
      axis->theta = val;
      return;
    }
    case FIELD_OFFS: {
      if ( axis->offset != CoordMax ) goto redef;
      axis->offset = val;
      return;
    }
  }
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT ) );
  return;

  redef:
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_DEF ) );
  return;

}


extern void TomotiltParseStoreOrient
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             Coord val)

{
  TomotiltOrient *orient;
  Size index;
  Status status;

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return;

  if ( tiltparse->parse->status ) return;

  if ( tiltparse->axisindex == TomotiltImageMax ) {
    ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_AXIS ) );
  }

  if ( tiltparse->state & STATE_ORIENT ) {
    index = tiltparse->orientindex;
    TomotiltParseCheck( index >= tomotilt->orients );
  } else {
    status = TomotiltNewOrient( tomotilt, tiltparse->axisindex, &index );
    if ( status ) {
      ParseError( tiltparse->parse, &err->loc, exception( status ) );
    } else {
      tiltparse->orientindex = index;
      tiltparse->state |= STATE_ORIENT;
    }
  }

  if ( tiltparse->parse->status ) return;

  orient = tomotilt->tiltorient;
  if ( TomotiltParseCheck( orient == NULL ) ) return;
  orient += index;

  switch ( type ) {
    case FIELD_PSI: {
      if ( orient->euler[0] != CoordMax ) goto redef;
      orient->euler[0] = val;
      return;
    }
    case FIELD_THE: {
      if ( orient->euler[1] != CoordMax ) goto redef;
      orient->euler[1] = val;
      return;
    }
    case FIELD_PHI: {
      if ( orient->euler[2] != CoordMax ) goto redef;
      orient->euler[2] = val;
      return;
    }
  }
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT ) );
  return;

  redef:
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_DEF ) );
  return;

}


static Size TomotiltParseGetImage
            (Tomotilt *tomotilt,
             Size number)

{

  for ( Size index = 0; index < tomotilt->images; index++ ) {
    if ( number == tomotilt->tiltimage[index].number ) return index;
  }

  return TomotiltImageMax;

}


extern void TomotiltParseImage
            (TomotiltParse *tiltparse,
             ParseSymb *err,
             Size number)

{
  TomotiltOrient *orient;
  Size index;
  Status status;

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return;

  if ( tiltparse->parse->status ) return;

  if ( tiltparse->axisindex == TomotiltImageMax ) {
    ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_AXIS ) );
  }

  if ( tiltparse->orientindex == TomotiltImageMax ) {
    status = TomotiltNewOrient( tomotilt, tiltparse->axisindex, &index );
    if ( status ) {
      ParseError( tiltparse->parse, &err->loc, exception( status ) );
    } else {
      orient = tomotilt->tiltorient;
      if ( TomotiltParseCheck( orient == NULL ) ) return;
      orient += index;
      tiltparse->orientindex = index;
    }
  }

  if ( tiltparse->parse->status ) return;

  tiltparse->imageindex = TomotiltImageMax;
  index = TomotiltParseGetImage( tomotilt, number );

  if ( index == TomotiltImageMax ) {

    status = TomotiltNewImage( tomotilt, tiltparse->axisindex,
                               tiltparse->orientindex, TomotiltImageMax, &index );
    if ( status ) {
      ParseError( tiltparse->parse, &err->loc, exception( status ) );
    } else {
      tomotilt->tiltimage[index].fileindex = TomotiltFileMax;
      tomotilt->tiltimage[index].number = number;
    }

  } else {

    if ( TomotiltParseCheck( index >= tomotilt->images ) ) return;
    if ( ( tomotilt->tiltgeom[index].axisindex != tiltparse->axisindex )
      || ( tomotilt->tiltgeom[index].orientindex != tiltparse->orientindex ) ) {
      ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_REDEF ) );
    }

  }

  if ( tiltparse->parse->status ) return;

  /* do not insert defaults for the time being
  if ( ( param->pixel > 0 ) && ( tomotilt->tiltimage[index].pixel <= 0 ) ) {
    tomotilt->tiltimage[index].pixel = param->pixel;
  }
  */

  tiltparse->imageindex = index;
  tiltparse->state &= ~( STATE_AXIS | STATE_ORIENT );
  tiltparse->state |= STATE_IMAGE;

}


extern void TomotiltParseStoreImage
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             const Coord *val,
             const Coord *val2)

{

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;
  if ( TomotiltParseCheckArg( ( val == NULL ) && ( type != FIELD_REF ) ) ) return;
  if ( TomotiltParseCheckArg( ( val2 == NULL ) && ( type == FIELD_DEFOC ) ) ) return;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return;

  if ( tiltparse->parse->status ) return;

  if ( tiltparse->imageindex == TomotiltImageMax ) {
    ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_IMAGE ) );
  }
  if ( TomotiltParseCheck( tiltparse->imageindex >= tomotilt->images ) ) return;

  if ( tiltparse->parse->status ) return;

  TomotiltAxis *axis = tomotilt->tiltaxis;
  TomotiltGeom *geom  = tomotilt->tiltgeom;
  TomotiltImage *image = tomotilt->tiltimage;
  if ( TomotiltParseCheck( axis  == NULL ) ) return;
  if ( TomotiltParseCheck( geom  == NULL ) ) return;
  if ( TomotiltParseCheck( image == NULL ) ) return;
  image += tiltparse->imageindex;
  geom  += tiltparse->imageindex;
  if ( TomotiltParseCheck( geom->axisindex >= tomotilt->axes ) ) return;
  axis +=geom->axisindex;

  switch ( type ) {
    case FIELD_REF: {
      if ( axis->cooref != TomotiltImageMax ) goto redef;
      axis->cooref = tiltparse->imageindex;
      return;
    }
    case FIELD_THETA: {
      if ( geom->theta != CoordMax ) goto redef;
      geom->theta = val[0];
      return;
    }
    case FIELD_ALPHA: {
      if ( geom->alpha != CoordMax ) goto redef;
      geom->alpha = val[0];
      return;
    }
    case FIELD_CORR: {
      if ( geom->corr[0] > 0 ) goto redef;
      if ( val[0] <= 0 ) goto value;
      if ( val[1] <= 0 ) goto value;
      geom->beta = val[2];
      geom->corr[0] = val[0];
      geom->corr[1] = val[1];
      return;
    }
    case FIELD_SCALE: {
      if ( geom->scale > 0 ) goto redef;
      if ( val[0] <= 0 ) goto value;
      geom->scale = val[0];
      return;
    }
    case FIELD_ORIG: {
      if ( geom->origin[0] != CoordMax ) goto redef;
      geom->origin[0] = val[0];
      geom->origin[1] = val[1];
      return;
    }
    case FIELD_PIXEL: {
      if ( image->pixel > 0 ) goto redef;
      if ( val[0] <= 0 ) goto value;
      image->pixel = val[0];
      return;
    }
    case FIELD_DEFOC: {
      if ( image->defocus != CoordMax ) goto redef;
      if ( val[0] > TomotiltValMax ) goto value;
      image->defocus = val[0];
      image->loc[0] = val2[0];
      image->loc[1] = val2[1];
      return;
    }
    case FIELD_ASTIG: {
      if ( image->ca > 0 ) goto redef;
      if ( val[0] <= 0 ) goto value;
      image->ca = val[0];
      image->phia = val[1];
      return;
    }
    case FIELD_AMPCO: {
      if ( image->ampcon != CoordMax ) goto redef;
      image->ampcon = val[0];
      return;
    }
  }
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT ) );
  return;

  redef:
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_DEF ) );
  return;

  value:
  ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_VAL ) );
  return;

}


static Status TomotiltParseGetFile
              (Tomotilt *tomotilt,
               const char *name,
               Size *fileindex)

{
  Status status;

  const char *tiltstrings = tomotilt->tiltstrings;
  if ( tiltstrings == NULL ) return exception( E_TOMOTILT );

  for ( Size index = 0; index < tomotilt->files; index++ ) {
    Size nameindex = tomotilt->tiltfile[index].nameindex;
    if ( !strcmp( name, tiltstrings + nameindex ) ) {
      *fileindex = index;
      return E_NONE;
    }
  }

  status = TomotiltNewFile( tomotilt, name, fileindex );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern void TomotiltParseStoreFile
            (TomotiltParse *tiltparse,
             ParseSymb *err,
             ParseSymb *sym)

{
  Status status;

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;
  if ( TomotiltParseCheckArg( sym == NULL ) ) return;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return;

  if ( tiltparse->parse->status ) return;

  if ( tiltparse->imageindex == TomotiltImageMax ) {
    ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_IMAGE ) );
  }

  if ( tiltparse->parse->status ) return;

  Size index = tomotilt->tiltimage[tiltparse->imageindex].fileindex;
  if ( index == TomotiltImageMax ) {

    status = TomotiltParseGetFile( tomotilt, sym->txt, &index );
    if ( exception( status ) ) {
      ParseError( tiltparse->parse, &sym->loc, exception( status ) );
    } else {
      tomotilt->tiltimage[tiltparse->imageindex].fileindex = index;
    }

  } else {

      ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_DEF ) );

  }

}


extern void TomotiltParseStoreFileOffs
            (TomotiltParse *tiltparse,
             ParseSymb *err,
             Index offs)

{

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return;

  if ( tiltparse->parse->status ) return;

  if ( tiltparse->imageindex == TomotiltImageMax ) {
    ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_IMAGE ) );
  }

  if ( tiltparse->parse->status ) return;

  Size index = tomotilt->tiltimage[tiltparse->imageindex].fileindex;
  if ( index == TomotiltImageMax ) {
    ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT ) );
  }

  if ( tiltparse->parse->status ) return;

  Size dim = ( offs == IndexMax ) ? 2 : 3;
  if ( tomotilt->tiltfile[index].dim ) {
    if ( tomotilt->tiltfile[index].dim != dim ) {
      ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT_OFFS ) );
    }
  } else {
    tomotilt->tiltfile[index].dim = dim;
  }
  if ( offs != IndexMax ) {
    if ( tomotilt->tiltimage[tiltparse->imageindex].fileoffset == INT64_MAX ) {
      tomotilt->tiltimage[tiltparse->imageindex].fileoffset = offs;
    } else {
      ParseError( tiltparse->parse, &err->loc, exception( E_TOMOTILT ) );
    }
  }

}


extern void TomotiltParseEnd
            (TomotiltParse *tiltparse,
             ParseSymb *err)

{

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return;
  if ( TomotiltParseCheckArg( err == NULL ) ) return;

  if ( tiltparse->parse->status ) return;

  tiltparse->state = STATE_END;

}


extern Status TomotiltParseCommit
              (TomotiltParse *tiltparse)

{
  Bool emdef = False;
  Bool pixundef = False;
  Bool focdef = False, focundef = False;
  Bool filedef = False, fileundef = False;
  Status emparam = E_NONE;
  Status pixel = E_NONE;
  Status defocus = E_NONE;
  Status file = E_NONE;
  Status axis = E_NONE;
  Status orient = E_NONE;
  Status theta = E_NONE;
  Status origin = E_NONE;
  Status status;

  if ( TomotiltParseCheckArg( tiltparse == NULL ) ) return E_TOMOTILT;

  Tomotilt *tomotilt = tiltparse->tomotilt;
  if ( TomotiltParseCheckArg( tomotilt == NULL ) ) return E_TOMOTILT;

  status = tiltparse->parse->status;
  if ( status ) goto exit;

  if ( !tomotilt->images ) {
    status = pushexception( E_TOMOTILT_EMPTY );
    goto exit;
  }

  for ( Size index = 0; index < tomotilt->files; index++ ) {
    TomotiltFile *file = tomotilt->tiltfile + index;
    if ( !file->dim ) {
      status = pushexception( E_TOMOTILT );
      goto exit;
    }
  }

  if ( tomotilt->param.euler[0] == CoordMax ) { tomotilt->param.euler[0] = 0; }
  if ( tomotilt->param.euler[1] == CoordMax ) { tomotilt->param.euler[1] = 0; }
  if ( tomotilt->param.euler[2] == CoordMax ) { tomotilt->param.euler[2] = 0; }
  if ( tomotilt->param.origin[0] == CoordMax ) { tomotilt->param.origin[0] = 0; }
  if ( tomotilt->param.origin[1] == CoordMax ) { tomotilt->param.origin[1] = 0; }
  if ( tomotilt->param.origin[2] == CoordMax ) { tomotilt->param.origin[2] = 0; }

  if ( ( tomotilt->param.emparam.cs > 0 ) || ( tomotilt->param.emparam.lambda > 0 )
    || ( tomotilt->param.emparam.fs > 0 ) || ( tomotilt->param.emparam.beta > 0 ) ) {
    if ( ( tomotilt->param.emparam.cs <= 0 ) || ( tomotilt->param.emparam.lambda <= 0 )
      || ( tomotilt->param.emparam.fs <  0 ) || ( tomotilt->param.emparam.beta < 0 ) ) {
      emparam = E_TOMOTILT_EMPARAM;
    }
    emdef = True;
  }

  for ( Size index = 0; index < tomotilt->images; index++ ) {
    TomotiltImage *image = tomotilt->tiltimage + index;
    TomotiltGeom *geom = tomotilt->tiltgeom + index;
    if ( image->fileindex == TomotiltFileMax ) { fileundef = True; } else { filedef = True; }
    if ( image->pixel <= 0 ) { pixundef = True; }
    if ( image->defocus == CoordMax ) { focundef = True; } else { focdef = True; }
    if ( ( ( image->ca > 0 ) || ( image->ampcon != CoordMax ) ) && ( image->defocus == CoordMax ) ) { defocus = E_TOMOTILT_DEFOC; }
    if ( image->phia == CoordMax ) { image->phia = 0; }
    if ( image->ampcon == CoordMax ) { image->ampcon = 0; }
    if ( geom->axisindex   == TomotiltImageMax ) { axis = E_TOMOTILT_AXIS; }
    if ( geom->orientindex == TomotiltImageMax ) { orient = E_TOMOTILT_ORIENT; }
    if ( geom->theta == CoordMax ) { theta = E_TOMOTILT_THETA; }
    if ( geom->alpha == CoordMax ) { geom->alpha = 0; }
    if ( geom->origin[0] == CoordMax ) { origin = E_TOMOTILT_ORIGIN; }
    if ( geom->origin[1] == CoordMax ) { origin = E_TOMOTILT_ORIGIN; }
  }

  if ( tomotilt->param.pixel > 0 ) { pixundef = False; }

  if ( emdef || focdef ) {
    if ( pixundef ) pixel = E_TOMOTILT_PIXEL;
  }
  if ( focdef ) {
    if (!emdef ) emparam = E_TOMOTILT_EMPARAM;
    if ( focundef ) defocus = E_TOMOTILT_DEFOC;
  }

  if ( filedef ) {
    if ( fileundef ) file = E_TOMOTILT_FILE;
  }

  Size refaxis = TomotiltImageMax;
  for ( Size index = 0; index < tomotilt->axes; index++ ) {
    TomotiltAxis *axis = tomotilt->tiltaxis + index;
    if ( ( refaxis == TomotiltImageMax ) && ( axis->cooref != TomotiltImageMax ) ) { refaxis = index; }
    if ( axis->phi == CoordMax ) { axis->phi = 0; }
    if ( axis->theta == CoordMax ) { axis->theta = 0; }
    if ( axis->offset == CoordMax ) { axis->offset = 0; }
  }

  for ( Size index = 0; index < tomotilt->orients; index++ ) {
    TomotiltOrient *orient = tomotilt->tiltorient + index;
    if ( orient->euler[0] == CoordMax ) { orient->euler[0] = 0; }
    if ( orient->euler[1] == CoordMax ) { orient->euler[1] = 0; }
    if ( orient->euler[2] == CoordMax ) { orient->euler[2] = 0; }
  }

  TomotiltAxis *tiltaxis = tomotilt->tiltaxis;
  if ( refaxis == TomotiltImageMax ) {
    Coord thetamin = CoordMax;
    for ( Size index = 0; index < tomotilt->images; index++ ) {
      if ( !tomotilt->tiltgeom[index].axisindex ) {
        Coord theta = fabs( tomotilt->tiltgeom[index].theta );
        if ( theta < thetamin ) {
          thetamin = theta;
          tiltaxis->cooref = index;
        }
      }
    }
  } else {
    tiltaxis += refaxis;
  }
  if ( tiltaxis->cooref < tomotilt->images ) {
    tomotilt->param.cooref = tiltaxis->cooref;
  } else {
    status = pushexception( E_TOMOTILT );
  }

  TomotiltSortNumber( tomotilt );

  if ( emparam ) status = pushexception( emparam );
  if ( pixel )   status = pushexception( pixel );
  if ( defocus ) status = pushexception( defocus );
  if ( file )    status = pushexception( file );
  if ( axis )    status = pushexception( axis );
  if ( orient )  status = pushexception( orient );
  if ( theta )   status = pushexception( theta );
  if ( origin )  status = pushexception( origin );

  exit:
  tiltparse->parse->status = status;
  if ( status ) {
    status = exception( E_TOMOTILT_PARSE );
  }

  return status;

}
