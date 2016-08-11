/*----------------------------------------------------------------------------*
*
*  imagicioopen.c  -  imageio: imagic files
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
#include "imageiocommon.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status ImagicImageFileOpen
              (Imageio *imageio)

{
  const char *hup = "DEH.", *iup = "GMI.";
  const char *hlo = "deh.", *ilo = "gmi.";
  const char *hdrpath;
  char *imgpath;
  Size len;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  Fileio *fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_IMAGICIO );

  ImagicMeta *meta = imageio->meta;
  if ( runcheck && ( meta == NULL ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( meta->hdrfile != NULL ) ) return pushexception( E_IMAGICIO );

  hdrpath = FileioGetPath( fileio );
  if ( hdrpath == NULL ) return pushexception( E_IMAGICIO );
  len = strlen( hdrpath );

  imgpath = strdup( hdrpath );
  if ( imgpath == NULL ) return pushexception( E_MALLOC );

  /* substitute .hed with .img */
  while ( len-- && *hup ) {
    if ( imgpath[len] == *hup ) {
      imgpath[len] = *iup;
    } else if ( imgpath[len] == *hlo ) {
      imgpath[len] = *ilo;
    } else {
      break;
    }
    hup++; iup++;
    hlo++; ilo++;
  } /* end while */

  if ( *hup ) {
    status = pushexception( E_IMAGICIO_NAME );
  } else {
    FileioParam param = FileioParamInitializer;
    param.mode = FileioGetMode( fileio );
    Fileio *imgfile = FileioOpen( imgpath, &param );
    status = testcondition( imgfile == NULL );
    if ( !status ) {
      Offset filesize = imageio->arrsize * TypeGetSize( imageio->eltype );
      if ( param.mode & IOCre ) {
        status = FileioAllocate( imgfile, filesize );
        if ( exception( status ) ) {
          FileioSetMode( imgfile, IODel );
        }
      } else {
        if ( FileioGetSize( imgfile ) < filesize ) {
          status = pushexception( E_IMAGICIO_ALLOC );
        }
      }
      if ( status ) {
        exception( FileioClose( imgfile ) );
      } else {
        meta->hdrfile = fileio;
        imageio->fileio = imgfile;
      }
    }
  }

  free( imgpath );

  return status;

}
