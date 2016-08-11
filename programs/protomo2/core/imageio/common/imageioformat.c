/*----------------------------------------------------------------------------*
*
*  imageioformat.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageioformat.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>
#include <string.h>


/* types */

typedef struct _ImageioFormatNode ImageioFormatNode;

struct _ImageioFormatNode {
  ImageioFormatNode *next;
  const ImageioFormat *format;
};


/* variables */

static const char ImageioFormatDefault[] = "FFF";

static ImageioFormatNode *ImageioFormatList = NULL;


/* functions */

extern Status ImageioFormatRegister
              (const ImageioFormat *format)

{
  ImageioFormatNode *node, *ptr;

  if ( argcheck( format == NULL ) ) return pushexception( E_ARGVAL );

  node = NULL;
  ptr = ImageioFormatList;
  while ( ptr != NULL ) {
    const ImageioFormat *fmt = ptr->format;
    if ( runcheck && ( fmt == NULL ) ) return pushexception( E_IMAGEIO );
    if ( runcheck && ( fmt->version.ident == NULL ) ) return pushexception( E_IMAGEIO );
    if ( fmt->prio <= format->prio ) break;
    node = ptr;
    ptr = ptr->next;
  }

  ptr = malloc( sizeof(ImageioFormatNode) );
  if ( ptr == NULL ) return pushexception( E_MALLOC );
  ptr->format = format;

  if ( node == NULL ) {
    ptr->next = ImageioFormatList;
    ImageioFormatList = ptr;
  } else {
    ptr->next = node->next;
    node->next = ptr;
  }

  return E_NONE;

}


static Status ImageioFormatGet
              (const char *ident,
               const ImageioFormat **fmtptr)

{

  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  const ImageioFormatNode *node = ImageioFormatList;
  while ( node != NULL ) {
    const ImageioFormat *fmt = node->format;
    if ( runcheck && ( fmt == NULL ) ) return exception( E_IMAGEIO );
    if ( runcheck && ( fmt->version.ident == NULL ) ) return exception( E_IMAGEIO );
    if ( !strcasecmp( fmt->version.ident, ident ) ) {
      *fmtptr = fmt; 
      return E_NONE;
    }
    node = node->next;
  }

  return exception( E_IMAGEIO_FMT );

}


extern const ImageioFormat *ImageioFormatNew
                            (const ImageioParam *param)

{
  const ImageioFormat *fmt;
  const char *ident = NULL;
  Status status;

  if ( param == NULL ) param = &ImageioParamDefault;

  if ( ( param->format == NULL ) || !*param->format ) {
    ident = ImageioFormatDefault;
  } else {
    ident = param->format;
  }
  if ( ident == NULL ) { pushexception( E_IMAGEIO_FMT ); return NULL; }

  status = ImageioFormatGet( ident, &fmt );
  if ( status == E_IMAGEIO_FMT ) { pushexceptionmsg( status, " ", ident ); return NULL; }
  if ( status ) { pushexception( status ); return NULL; }

  return fmt;

}


extern Status ImageioFormatOld
              (const ImageioParam *param,
               Imageio *imageio)

{
  const ImageioFormat *fmt;
  Status status;

  if ( param == NULL ) param = &ImageioParamDefault;

  if ( ( param->format == NULL ) || !*param->format ) {

    imageio->iostat |= ImageioFmtAuto;

    const ImageioFormatNode *node = ImageioFormatList;
    while ( node != NULL ) {
      fmt = node->format;
      if ( runcheck && ( fmt == NULL ) ) return pushexception( E_IMAGEIO );
      if ( runcheck && ( fmt->version.ident == NULL ) ) return pushexception( E_IMAGEIO );
      if ( fmt->fmt == NULL ) return pushexception( E_IMAGEIO );
      imageio->format = fmt;
      status = fmt->fmt( imageio );
      if ( !popexception( status ) ) return E_NONE;
      imageio->format = NULL;
      node = node->next;
    }
    status = pushexception( E_IMAGEIO_FMT );

  } else {

    imageio->iostat &= ~ImageioFmtAuto;

    status = ImageioFormatGet( param->format, &fmt );
    if ( status == E_IMAGEIO_FMT ) {
      pushexceptionmsg( status, " ", param->format );
    } else if ( status ) {
      pushexception( status );
    } else {
      if ( fmt->fmt == NULL ) return pushexception( E_IMAGEIO );
      imageio->format = fmt;
      status = fmt->fmt( imageio );
      if ( !exception( status ) ) return E_NONE;
      imageio->format = NULL;
      pushexception( status );
    }

  }

  return status;

}


extern Status ImageioFormatCheck
              (const char *format)

{
  const ImageioFormat *fmt;
  Status status;

  status = ImageioFormatGet( format, &fmt );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern void *ImageioGetFormatOpt
             (const char *format)

{
  const ImageioFormat *fmt;
  Status status;

  status = ImageioFormatGet( format, &fmt );
  if ( exception( status ) ) return NULL;

  return fmt->opt;

}
