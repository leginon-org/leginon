/*----------------------------------------------------------------------------*
*
*  i3data.h  -  io: i3 data
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef i3data_h_
#define i3data_h_

#include "iodefs.h"
#include "i3datadefs.h"

#define I3dataName   "i3data"
#define I3dataVers   IOVERS"."IOBUILD
#define I3dataCopy   IOCOPY


/* exception codes */

enum {
  E_I3DATA = I3dataModuleCode,
  E_I3DATA_IMPL,
  E_I3DATA_ENT,
  E_I3DATA_NOENT,
  E_I3DATA_MAXCODE
};


/* types */

typedef enum {
  I3dataFlagHdr   = 0x01,
  I3dataFlagEnt   = 0x02,
  I3dataFlagData  = 0x04,
  I3dataFlagCopy  = 0x08,
  I3dataFlagList  = 0x10,
  I3dataFlagPrint = 0x20,
} I3dataFlags;

typedef struct {
  I3dataCode code;
  const char *name;
  Size count;
  Size elcount;
  Size elsize;
  Size uncount;
  Size unelsize;
  I3dataFlags flags;
} I3dataDscr;

struct _I3data;

typedef struct _I3data I3data;

struct _I3data {
  Status (*init)( void *, I3data * );
  Status (*final)( I3data *, Status );
  Status (*read)( const I3data *,  int, Size *, void * );
  Status (*readbuf)( const I3data *,  int, Size *, void ** );
  Status (*finalbuf)( const I3data *,  int, void * );
  Status (*unpack)( int, Size, const void *, void * );
  Status (*pack)( int, Size, const void *, void * );
  Status (*write)( const I3data *,  int, Size, const void * );
  Status (*writenew)( const I3data *,  int, Size, const void * );
  void *handle;
};


/* constants */

#define I3dataInitializer  (I3data){ NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL }


/* prototypes */

extern Status I3dataGetImage
              (const Image *image,
               I3Image *i3image);

extern const I3dataDscr *I3dataGetDscr
                         (int code);

extern Status I3dataIter
              (Status (*call)(const I3dataDscr *, const void *, void * ),
               const void *src,
               void *dst,
               I3dataFlags flags);

extern void I3dataPrint
            (int code,
             Size count,
             const void *buf);

extern Status I3dataRegister
              (const I3dataDscr table[]);


#endif
