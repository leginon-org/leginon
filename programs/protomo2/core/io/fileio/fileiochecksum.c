/*----------------------------------------------------------------------------*
*
*  fileiochecksum.c  -  io: file i/o
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
#include "fileiochecksum.h"
#include "exception.h"
#include <string.h>
#include <unistd.h>


/* constants */

#define BUFLEN       512
#define CMPLEN       4096


/* functions */

extern Status FileioChecksum
              (const Fileio *fileio,
               ChecksumType type,
               Size buflen,
               uint8_t *buf)

{
  uint8_t rdbuf[BUFLEN];
  Status status;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buflen < 4 ) ) return exception( E_ARGVAL );

  if ( ( type <= ChecksumTypeUndef ) || ( type >= ChecksumTypeMax ) ) return exception( E_FILEIO );

  memset( buf, 0, buflen );

  buf[1] = buflen - 2;
  if ( buf[1] != buflen - 2 ) return exception( E_FILEIO );

  Offset offset = 0;
  Size length = ( CMPLEN < fileio->stat.size ) ? CMPLEN : fileio->stat.size;

  while ( length ) {

    Offset rdoffs = lseek( fileio->filedscr, offset, SEEK_SET );
    if ( rdoffs != offset ) {
      return exception( E_ERRNO );
    }

    Size count = ( length < BUFLEN ) ? length : BUFLEN;
    ssize_t rdcount = read( fileio->filedscr, rdbuf, count );
    if ( rdcount != (ssize_t)count ) {
      if ( rdcount == 0 ) return exception( E_EOF );
      if ( rdcount >  0 ) return exception( E_FILEIO_READ );
      if ( rdcount <  0 ) return exception( E_ERRNO );
    }

    status = ChecksumCalc( type, count, rdbuf, buflen - 2, buf + 2 );
    if ( exception( status ) ) return status;

    offset += count;
    length -= count;

  }

  buf[0] = type;

  return E_NONE;

}
