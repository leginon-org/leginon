/*----------------------------------------------------------------------------*
*
*  tomoparamsemant.h  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoparamsemant_h_
#define tomoparamsemant_h_

#include "tomoparamcommon.h"


/* prototypes */

extern void TomoparamPushStk
            (Tomoparam *tomoparam,
             const ParseSymb *symb);

extern void TomoparamPopStk
            (Tomoparam *tomoparam,
             const ParseSymb *symb);

extern void TomoparamPushSection
            (Tomoparam *tomoparam,
             const ParseSymb *symb,
             const ParseSymb *start);

extern void TomoparamPopSection
            (Tomoparam *tomoparam,
             const ParseSymb *symb);

extern void TomoparamSetVar
            (Tomoparam *tomoparam,
             const ParseSymb *id,
             const ParseSymb *op,
             const TomoparamVar *src);

extern TomoparamVar TomoparamGetVar
                    (const Tomoparam *tomoparam,
                     const ParseSymb *id);

extern TomoparamVar TomoparamGetArray
                    (Tomoparam *tomoparam,
                     const ParseSymb *symb);

extern void TomoparamElement
            (Tomoparam *tomoparam,
             const TomoparamVar *var);

extern TomoparamVar TomoparamUnOp
                    (Tomoparam *tomoparam,
                     const ParseSymb *op,
                     TomoparamVar *src);

extern TomoparamVar TomoparamBinOp
                    (Tomoparam *tomoparam,
                     TomoparamVar *src1,
                     const ParseSymb *op,
                     TomoparamVar *src2);

extern TomoparamVar TomoparamMulOp
                    (Tomoparam *tomoparam,
                     TomoparamVar *src1,
                     TomoparamVar *src2);


#endif
