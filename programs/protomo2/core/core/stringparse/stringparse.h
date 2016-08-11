/*----------------------------------------------------------------------------*
*
*  stringparse.h  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef stringparse_h_
#define stringparse_h_

#include "defs.h"

#define StringParseName   "stringparse"
#define StringParseVers   COREVERS"."COREBUILD
#define StringParseCopy   CORECOPY


/* exception codes */

enum {
  E_STRINGPARSE = StringParseModuleCode,
  E_STRINGPARSE_ERROR,
  E_STRINGPARSE_NOPARSE,
  E_STRINGPARSE_SEPAR,
  E_STRINGPARSE_MAXCODE
};


/* types */

union _StringParseParam;

typedef Status (*StringParse)( const char *, const char **, void *, union _StringParseParam * );

typedef union _StringParseParam {
  Size dstsize;
  struct {
    Size dstsize;
    const char *ptr;
  } string;
  struct {
    Size dstsize;
    const char *extra;
  } ident;
  struct {
    Size dstsize;
    const char *extra;
    const char **table;
    Bool exact;
  } keyword;
  struct {
    Size dstsize;
    Size base;
  } number;
  struct {
    Size dstsize;
    StringParse parse;
    Bool single;
    Bool space;
    char sep;
  } pair;
  struct {
    Size dstsize;
    StringParse parse;
    union _StringParseParam *param;
    Size count;
    Bool space;
    char sep;
  } list;
  struct {
    Size dstsize;
    StringParse parse;
    Bool empty;
    Bool lower;
    Bool dotdot;
    Bool upper;
  } range;
  struct {
    Size dstsize;
    Size count;
    Size min;
    Size max;
    Bool space;
    Bool empty;
  } selection;
} StringParseParam;


/* constants */

#define StringParseParamInitializer  (StringParseParam){ 0 }


/* prototypes */

extern Status StringParseBool
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseUint8
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseUint16
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseUint32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseUint64
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseInt8
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseInt16
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseInt32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseInt64
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseReal32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseReal64
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseImag32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseImag64
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseCmplx32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseCmplx64
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParsePair
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseRange
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseList
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseSelection
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseString
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseStringCase
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseIdent
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseKeyword
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseKeywordCase
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);

extern Status StringParseDateTime
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param);


#if IndexBits == 32

  #define StringParseIndex   StringParseInt32

#elif IndexBits == 64

  #define StringParseIndex   StringParseInt64

#endif


#if SizeBits == 32

  #define StringParseSize   StringParseUint32

#elif SizeBits == 64

  #define StringParseSize   StringParseUint64

#endif


#if OffsetBits == 32

  #define StringParseOffset   StringParseInt32

#elif OffsetBits == 64

  #define StringParseOffset   StringParseInt64

#endif


#if CoordBits == 32

  #define StringParseCoord   StringParseReal32

#elif CoordBits == 64

  #define StringParseCoord   StringParseReal64

#endif


#if RealBits == 32

  #define StringParseReal   StringParseReal32
  #define StringParseImag   StringParseImag32
  #define StringParseCmplx  StringParseCmplx32

#elif RealBits == 64

  #define StringParseReal   StringParseReal64
  #define StringParseImag   StringParseImag64
  #define StringParseCmplx  StringParseCmplx64

#endif


#endif
