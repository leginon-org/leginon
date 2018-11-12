/*----------------------------------------------------------------------------*
*
*  imagiciotypes.c  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include <ctype.h>
#include <exception.h>


/* Imagic data types */

static const ImagicType ImagicTypeTable[] = { 
  { "PACK", TypeUint8,	 ImageRealspc },
  { "INTG", TypeInt16,   ImageRealspc },
  { "LONG", TypeInt32,   ImageRealspc },
  { "REAL", TypeReal32,  ImageRealspc },
  { "COMP", TypeCmplx32, ImageFourspc },
  { "RECO", TypeCmplx32, ImageRealspc },
  {  NULL,  0,           0,           }
};


/* functions */

extern Status ImagicGetType
              (const ImagicHeader *hdr,
               Type *type,
               ImageAttr *attr)

{
  const ImagicType *ptr = ImagicTypeTable;
  int t0 = toupper( hdr->type[0] );
  int t1 = toupper( hdr->type[1] );
  int t2 = toupper( hdr->type[2] );
  int t3 = toupper( hdr->type[3] );

  if ( ( hdr->cmplx < 0 ) || ( hdr->cmplx > 1 ) ) {
    return exception( E_IMAGEIO_TYPE );
  }

  while ( ptr->name != NULL ) {
    if ( ( ptr->name[0] == t0 )
      && ( ptr->name[1] == t1 )
      && ( ptr->name[2] == t2 )
      && ( ptr->name[3] == t3 ) ) {
      if ( type != NULL ) *type = ptr->type;
      if ( attr != NULL ) *attr = ptr->attr;
      return E_NONE;
    }
    ptr++;
  }

  return exception( E_IMAGEIO_TYPE );

}


extern Status ImagicSetType
              (Type type,
               ImageAttr attr,
               ImagicHeader *hdr)

{
  const ImagicType *ptr = ImagicTypeTable;

  while ( ptr->name != NULL ) {
    if ( ptr->type == type ) {
      hdr->type[0] = ptr->name[0];
      hdr->type[1] = ptr->name[1];
      hdr->type[2] = ptr->name[2];
      hdr->type[3] = ptr->name[3];
      return E_NONE;
    }
    ptr++;
  }

  return exception( E_IMAGEIO_TYPE );

}
