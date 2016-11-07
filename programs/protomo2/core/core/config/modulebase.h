/*----------------------------------------------------------------------------*
*
*  modulebase.h  -  configuration
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef modulebase_h_
#define modulebase_h_


/* module base codes */

#define CoreModuleBase           0x00000000
#define StartupModuleBase        0x00010000
#define OptionsModuleBase        0x00020000

#define ArrayModuleBase          0x00040000
#define ImageModuleBase          0x00050000
#define TypeModuleBase           0x00070000

#define FourierModuleBase        0x00080000
#define FourieropModuleBase      0x00090000

#define ApproxModuleBase         0x00100000

#define IOModuleBase             0x00200000
#define ImageioModuleBase        0x00210000

#define ObjectModuleBase         0x00300000
#define ObjectioModuleBase       0x00310000

#endif
