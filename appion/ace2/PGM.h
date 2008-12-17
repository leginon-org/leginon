#ifndef libcv_pgm
#define libcv_pgm 

#include "Array.h"

@interface Array ( PGM_File )

+ (ArrayP) readPGMFile: (char *)filename ;
- (u32)    writePGMFile: (char *)filename ;

@end

#endif
