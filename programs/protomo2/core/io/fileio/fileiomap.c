/*----------------------------------------------------------------------------*
*
*  fileiomap.c  -  io: file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fileiocommon.h"
#include "exception.h"
#include "macros.h"
#include <sys/mman.h>
#include <unistd.h>


/* functions */

extern Status FileioMap
              (Fileio *fileio,
               Offset offset,
               Size length)

{
  Offset maplength;
  Status status = E_NONE;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( offset < 0 ) {
    return exception( E_ARGVAL );
  }
  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }
  if ( fileio->iostatus & FileioStdio ) {
    return exception( E_FILEIO_IOSET );
  }

  if ( length ) {
    if ( length > (Size)OffsetMaxSize ) {
      return exception( E_INTOVFL );
    }
    maplength = length;
  } else {
    maplength = fileio->stat.size;
    if ( offset < maplength ) {
      maplength -= offset;
      if ( maplength > OffsetMaxSize ) {
        return exception( E_INTOVFL );
      }
    } else {
      maplength = 0;
    }
    length = maplength;
  }

  if ( maplength > 0 ) {

    if ( ( fileio->iostatus & FileioMapio ) && ( offset >= fileio->mapoffset ) ) {

      Offset offs = offset - fileio->mapoffset;
      if ( OFFSETADDOVFL( offs, maplength ) ) return exception( E_INTOVFL );

      if ( ( offs + maplength <= (Offset)fileio->maplength ) ) {
        fileio->mapaddrbase = offs;
        return E_NONE;
      }

    }

    long int pagesize = sysconf( _SC_PAGESIZE );
    Offset base = offset % pagesize;
    offset -= base;

    if ( OFFSETADDOVFL( maplength, base ) ) return exception( E_INTOVFL );
    maplength += base;

    if ( maplength > OffsetMaxSize ) return exception( E_INTOVFL );
    length = maplength;

    if ( OFFSETADDOVFL( offset, maplength ) ) return exception( E_INTOVFL );
    Offset filesize = offset + maplength;

    if ( filesize > fileio->stat.size ) {
      if ( fileio->mode & IOWr ) {
        status = FileioAllocate( fileio, filesize );
        if ( exception( status ) ) return status;
      } else {
        return exception( E_FILEIO_SIZE );
      }
    }

    if ( fileio->maplength ) {
      if ( munmap( fileio->mapaddr, fileio->maplength ) ) {
        return exception( E_ERRNO );
      }
      fileio->maplength = 0;
    }
    fileio->iostatus &= ~FileioModio;

    int flags = PROT_READ;
    if ( fileio->mode & IOWr ) flags |= PROT_WRITE;

    if ( length ) {

      fileio->mapaddr = mmap( NULL, length, flags, MAP_SHARED, fileio->filedscr, offset );
      if ( fileio->mapaddr == MAP_FAILED ) {
        return exception( E_ERRNO );
      } else if ( fileio->mapaddr == NULL ) {
        return exception( E_FILEIO_MMAP ); /* mmap returns NULL sometimes ?? */
      }

      fileio->maplength = length;
      fileio->mapoffset = offset;
      fileio->mapaddrbase = base;

    } else {

      fileio->mapaddr = NULL;
      fileio->maplength = 0;

    }

  }

  fileio->iostatus |= FileioMapio;

  return E_NONE;

}
