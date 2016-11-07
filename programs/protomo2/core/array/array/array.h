/*----------------------------------------------------------------------------*
*
*  array.h  -  array: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef array_h_
#define array_h_

#include "arraydefs.h"

#define ArrayName   "array"
#define ArrayVers   ARRAYVERS"."ARRAYBUILD
#define ArrayCopy   ARRAYCOPY


/* exception codes */

enum {
  E_ARRAY = ArrayModuleCode,
  E_ARRAY_DIM,
  E_ARRAY_ZERO,
  E_ARRAY_BOUNDS,
  E_ARRAY_MAXCODE
};


/* types */

typedef Status (*ArraySrcFn)( Offset, Size, Size, void *, void * );
typedef Status (*ArrayCpyFn)( Size, Size, const void *, Size, void *, void * );
typedef Status (*ArrayDstFn)( Offset, Size, Size, const void *, void * );


/* prototypes */

extern Status ArraySize
              (Size dim,
               const Size *len,
               Size elsize,
               Size *size);

extern Status ArrayOffset
              (Size dim,
               const Size *len,
               Size elsize,
               Offset *offs);

extern Status ArrayElement
              (Size dim,
               const Size *len,
               Size elsize,
               const Size *ind,
               Size *el);

extern Status ArrayElementOffs
              (Size dim,
               const Size *len,
               Size elsize,
               const Size *ind,
               Offset *el);

extern Status ArrayBox
              (Size dim,
               const Size *len,
               const Size *ori,
               const Size *box,
               Size *dst,
               Size *size);

extern Status ArrayBoxCtr
              (Size dim,
               const Size *len,
               const Size *ctr,
               const Size *box,
               Size *ori,
               Size *pos,
               Size *dst,
               Size *size);

extern Status ArrayFill
              (Size dim,
               const void *srcaddr,
               const Size *dstlen,
               void *dstaddr,
               Size elsize);

extern Status ArrayCut
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               void *dstaddr,
               Size elsize);

extern Status ArrayCutClip
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               Size *dstlen,
               void *dstaddr,
               Size elsize);

extern Status ArrayCutCyc
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               void *dstaddr,
               Size elsize);

extern Status ArrayCutPaste
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               void *dstaddr,
               Size elsize);

extern Status ArrayCutPasteClip
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size *cutlen,
               void *dstaddr,
               Size elsize);

extern Status ArrayCutPasteCyc
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               void *dstaddr,
               Size elsize);

extern Status ArrayFnBox
              (Size dim,
               const Size *len,
               const Size *ori,
               const Size *box,
               Size elsize,
               Size *dst,
               Offset *size);

extern Status ArrayFnBoxCtr
              (Size dim,
               const Size *len,
               const Size *ctr,
               const Size *box,
               Size elsize,
               Size *ori,
               Size *pos,
               Size *dst,
               Offset *size);

extern Status ArrayFnCut
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data);

extern Status ArrayFnCutClip
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data);

extern Status ArrayFnCutCyc
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data);

extern Status ArrayFnCutPaste
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data);

extern Status ArrayFnCutPasteClip
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               Size *cutlen,
               void *data);

extern Status ArrayFnCutPasteCyc
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data);


#endif
