/*----------------------------------------------------------------------------*
*
*  i3io.h  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef i3io_h_
#define i3io_h_

#include "fileio.h"

#define I3ioName   "i3io"
#define I3ioVers   IOVERS"."IOBUILD
#define I3ioCopy   IOCOPY


/* exception codes */

enum {
  E_I3IO = I3ioModuleCode,
  E_I3IO_OFF,
  E_I3IO_LEN,
  E_I3IO_MAXCODE
};


/* types */

struct _I3io;

typedef struct _I3io I3io;

typedef struct {
  const char *filepath;
  Size initsegm;
  Offset initsize;
  IOMode mode;
} I3ioParam;

typedef uint64_t I3ioMeta;


/* constants */

#define I3ioParamInitializer  (I3ioParam){ NULL, 0, 0, 0 }


/* prototypes */

extern I3io *I3ioCreate
             (const char *path,
              const I3ioParam *param);

extern I3io *I3ioCreateOnly
             (const char *path,
              const I3ioParam *param);

extern I3io *I3ioTemp
             (const char *path,
              const I3ioParam *param);

extern I3io *I3ioOpenReadOnly
             (const char *path,
              const I3ioParam *param);

extern I3io *I3ioOpenReadWrite
             (const char *path,
              const I3ioParam *param);

extern I3io *I3ioOpenUpdate
             (const char *path,
              const I3ioParam *param);

extern I3io *I3ioInit
             (Fileio *fileio,
              Offset offset,
              const I3ioParam *param);

extern Status I3ioFlush
              (I3io *i3io);

extern Status I3ioClose
              (I3io *i3io,
               Status fail);

extern Status I3ioAddr
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               void **addr);

extern Status I3ioRead
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               void *buf);

extern void *I3ioReadBuf
             (I3io *i3io,
              int segm,
              Offset offs,
              Size size);

extern void *I3ioReadSegm
             (I3io *i3io,
              int segm,
              Size *size);

extern Status I3ioWrite
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               const void *buf);

extern Status I3ioWriteSegm
              (I3io *i3io,
               int segm,
               Size size,
               const void *buf);

extern Status I3ioWriteAlloc
              (I3io *i3io,
               int segm,
               Size size,
               const void *buf,
               I3ioMeta meta);

extern void *I3ioBeginRead
             (I3io *i3io,
              int segm,
              Offset offs,
              Size size);

extern void *I3ioBeginWrite
             (I3io *i3io,
              int segm,
              Offset offs,
              Size size);

extern Status I3ioEndRead
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               void *addr);

extern Status I3ioEndWrite
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               void *addr);

extern void *I3ioBeginReadSegm
             (I3io *i3io,
              int segm,
              Size *size);

extern void *I3ioBeginWriteSegm
             (I3io *i3io,
              int segm,
              Size *size);

extern Status I3ioEndReadSegm
              (I3io *i3io,
               int segm,
               void *addr);

extern Status I3ioEndWriteSegm
              (I3io *i3io,
               int segm,
               void *addr);

extern void *I3ioBeginWriteAlloc
             (I3io *i3io,
              int segm,
              Size size,
              I3ioMeta meta);

extern Status I3ioEndWriteAlloc
              (I3io *i3io,
               int segm,
               Size size,
               void *addr,
               Status fail);

extern Status I3ioSegm
              (I3io *i3io,
               Offset size,
               I3ioMeta meta,
               int *segm);

extern Status I3ioAlloc
              (I3io *i3io,
               int segm, 
               Offset size,
               I3ioMeta meta);

extern Status I3ioDealloc
              (I3io *i3io,
               int segm);

extern Status I3ioResize
              (I3io *i3io,
               int segm,
               Offset size);

extern Status I3ioAccess
              (I3io *i3io,
               int segm,
               Offset *offs,
               Offset *size,
               I3ioMeta *meta);

extern Status I3ioMetaSet
              (I3io *i3io,
               int index,
               I3ioMeta meta);

extern Status I3ioMetaGet
              (I3io *i3io,
               int index,
               I3ioMeta *meta);

extern I3ioMeta *I3ioFormat
                 (void *buf,
                  Size len);

extern const char *I3ioGetPath
                   (I3io *i3io);

extern Bool I3ioGetSwap
            (I3io *i3io);

extern IOMode I3ioGetMode
              (I3io *i3io);

extern void I3ioGetTime
            (I3io *i3io,
             Time *cre,
             Time *mod);

extern Status I3ioGetChecksum
              (I3io *i3io,
               Size sumlen,
               uint8_t *sum);


#endif
