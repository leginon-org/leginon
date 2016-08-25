/*----------------------------------------------------------------------------*
*
*  i3iofile.c  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3iocommon.h"
#include "heapproc.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static I3io *I3ioFileInit
             (Fileio *fileio,
              Offset offset,
              const I3ioParam *param)

{
  Status status;

  if ( sizeof(I3ioMeta) > sizeof(HeapMeta) ) {
    pushexception( E_I3IO ); return NULL;
  }

  IOMode mode = FileioGetMode( fileio );
  mode &= IONew | IOCre | IOFd | IOExt | IOMod | IOWr | IORd | IOMmp | IOShr | IOXcl | IOLck;

  IOMode mask = IOExt | IOMod | IOWr | IOBuf;
  mode = ( mode & ~mask ) | ( param->mode & mode & ( mask | IOFd | IOBuf ) );

  mask = IONew | IOCre;
  if ( ( mode & mask ) && !( param->mode & mask ) ) {
    pushexception( E_ARGVAL ); return NULL;
  }

  HeapParam hpar = HeapParamInitializer;
  hpar.mode = mode;
  hpar.initsegm = param->initsegm;
  hpar.initsize = param->initsize;

  HeapFileParam fpar = HeapFileParamInitializer;
  fpar.param = &hpar;
  fpar.offs = offset;

  Heap *heap = HeapFileInit( fileio, &fpar );
  status = testcondition( heap == NULL );
  if ( status ) return NULL;

  return (I3io *)heap;

}


static I3io *I3ioFileOpen
             (const char *path,
              const IOMode mode,
              const I3ioParam *param)

{
  Status status;

  if ( argcheck( path == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  I3ioParam iopar = ( param == NULL ) ? I3ioParamInitializer : *param;
  iopar.mode &= IOMmp | IOShr | IOXcl | IOLck | IOBuf | IODel;
  iopar.mode |= mode | IORd;

  FileioParam fpar = FileioParamInitializer;
  fpar.filepath = iopar.filepath;
  fpar.mode = iopar.mode;

  Fileio *fileio = FileioOpen( path, &fpar );
  status = testcondition( fileio == NULL );
  if ( status ) return NULL;

  if ( iopar.mode & IOMmp ) {
    status = FileioMap( fileio, 0, 0 );
    if ( exception( status ) ) {
      status = FileioMap( fileio, OffsetMax, 0 );
      if ( pushexception( status ) ) return NULL;
    }
  }

  I3io *i3io = I3ioFileInit( fileio, 0, &iopar );
  status = testcondition( i3io == NULL );
  if ( status ) goto error;

  return i3io;

  error:

  FileioSetMode( fileio, IODel );
  status = FileioClose( fileio );
  logexception( status );

  return NULL;

}


extern I3io *I3ioCreate
             (const char *path,
              const I3ioParam *param)

{

  if ( argcheck( path == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  return I3ioFileOpen( path, IOCre | IOExt, param );

}


extern I3io *I3ioCreateOnly
             (const char *path,
              const I3ioParam *param)

{

  if ( argcheck( path == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  return I3ioFileOpen( path, IONew | IOExt, param );

}


extern I3io *I3ioTemp
             (const char *path,
              const I3ioParam *param)

{

  return I3ioFileOpen( path, IOTmp | IOExt, param );

}


extern I3io *I3ioOpenReadOnly
             (const char *path,
              const I3ioParam *param)

{

  if ( argcheck( path == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  return I3ioFileOpen( path, IOOld, param );

}


extern I3io *I3ioOpenReadWrite
             (const char *path,
              const I3ioParam *param)

{

  return I3ioFileOpen( path, IOOld | IOMod, param );

}


extern I3io *I3ioOpenUpdate
             (const char *path,
              const I3ioParam *param)

{

  return I3ioFileOpen( path, IOOld | IOExt, param );

}


extern I3io *I3ioInit
             (Fileio *fileio,
              Offset offset,
              const I3ioParam *param)

{
  Status status;

  if ( fileio == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  const I3ioParam *iopar = ( param == NULL ) ? &I3ioParamInitializer : param;
  I3io *i3io = I3ioFileInit( fileio, offset, iopar );
  status = testcondition( i3io == NULL );
  if ( status ) return NULL;

  return i3io;

}
