/*----------------------------------------------------------------------------*
*
*  fileio.h  -  io: file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fileio_h_
#define fileio_h_

#include "iodefs.h"

#define FileioName   "fileio"
#define FileioVers   IOVERS"."IOBUILD
#define FileioCopy   IOCOPY


/* exception codes */

enum {
  E_FILEIO = FileioModuleCode,
  E_FILEIO_CREAT,
  E_FILEIO_MODE,
  E_FILEIO_OPEN,
  E_FILEIO_USE,
  E_FILEIO_DEL,
  E_FILEIO_IOSET,
  E_FILEIO_IOCHK,
  E_FILEIO_PERM,
  E_FILEIO_MMAP,
  E_FILEIO_COUNT,
  E_FILEIO_SIZE,
  E_FILEIO_READ,
  E_FILEIO_WRITE,
  E_FILEIO_MAXCODE
};


/* types */

struct _Fileio;

typedef struct _Fileio Fileio;

typedef struct {
  IOMode mode;
  const char *filepath;
} FileioParam;


/* constants */

#define FileioParamInitializer  (FileioParam){ 0, NULL }


/* prototypes */

extern Fileio *FileioOpen
               (const char *path,
                const FileioParam *param);

extern Fileio *FileioOpenStd
               (const char *path,
                const FileioParam *param);

extern Fileio *FileioOpenMap
               (const char *path,
                const FileioParam *param);

extern Status FileioClose
              (Fileio *fileio);

extern Status FileioDestroy
              (Fileio *fileio);

extern Status FileioUnlink
              (Fileio *fileio);

extern Status FileioStd
              (Fileio *fileio);

extern Status FileioMap
              (Fileio *fileio,
               Offset offset,
               Size length);

extern Status FileioUnmap
              (Fileio *fileio);

extern Status FileioAllocate
              (Fileio *fileio,
               Offset size);

extern Status FileioTruncate
              (Fileio *fileio,
               Offset size);

extern Status FileioFlush
              (Fileio *fileio);

extern Status FileioRead
              (Fileio *fileio,
               Offset offset,
               Size length,
               void *addr);

extern Status FileioReadStd
              (Fileio *fileio,
               Offset offset,
               Size length,
               void *addr);

extern Status FileioWrite
              (Fileio *fileio,
               Offset offset,
               Size length,
               const void *addr);

extern Status FileioWriteStd
              (Fileio *fileio,
               Offset offset,
               Size length,
               const void *addr);

extern Status FileioAccess
              (const Fileio *fileio,
               Offset *size,
               void **addr,
               Size *length,
               Offset *offset);

extern Status FileioReadLock
              (Fileio *fileio,
               Offset offset,
               Size length);

extern Status FileioWriteLock
              (Fileio *fileio,
               Offset offset,
               Size length);

extern Status FileioUnlock
              (Fileio *fileio,
               Offset offset,
               Size length);

extern Status FileioStatusStd
              (Fileio *fileio,
               Bool *flag);

extern Status FileioStatusMap
              (Fileio *fileio,
               Bool *flag);

extern Status FileioStatusMod
              (Fileio *fileio,
               Bool *flag);

extern Status FileioSetFileMode
              (const Fileio *fileio);

extern Status FileioSetMode
              (Fileio *fileio,
               IOMode mode);

extern Status FileioClearMode
              (Fileio *fileio,
               IOMode mode);

extern const char *FileioGetPath
                   (const Fileio *fileio);

extern const char *FileioGetFullPath
                   (const Fileio *fileio);

extern int FileioGetFd
           (const Fileio *fileio);

extern IOMode FileioGetMode
              (const Fileio *fileio);

extern Offset FileioGetSize
              (const Fileio *fileio);

extern void *FileioGetAddr
             (const Fileio *fileio);


#endif
