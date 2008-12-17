#ifndef libcv_png
#define libcv_png

#include <png.h>
#include "Array.h"
#include "util.h"

@interface	Array ( PNG_File )

+ (ArrayP) readPNGFile: (char *)filename ;
- (u32)    writePNGFile: (char *)filename ;

@end

#endif

