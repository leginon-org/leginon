/*
*  config.h: for gcc4
*
*  Copyright © 2012 Hanspeter Winkler
*
*/

/* use POSIX standard */
#ifndef _POSIX_C_SOURCE
  #define _POSIX_C_SOURCE 200809L
#endif

/* for fdopen, fseeko, fchmod, fsync, ftruncate */
#ifndef _BSD_SOURCE
  #define _BSD_SOURCE
#endif

/* extra functions fseeko and ftello */
#ifndef _LARGEFILE_SOURCE
  #define _LARGEFILE_SOURCE
#endif

/* size of type off_t */
#ifdef ENABLE_LARGEFILES
  #define OFFSETBITS 64
  #define _FILE_OFFSET_BITS 64
#else
  #define OFFSETBITS 32
  #undef _FILE_OFFSET_BITS
#endif

/* when using POSIX threads */
