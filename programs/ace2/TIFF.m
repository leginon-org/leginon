#include "TIFF.h"

@implementation Array ( TIFF_File )

-(u32) writeTIFFFile:(char *)filename {
	
	TIFF * tiff_file = TIFFOpen(filename,"w");
	TIFFSetDirectory(tiff_file,0);
	
	f32 * data = [self dataAsType: TYPE_F32 withFlags:CV_COPY_DATA];
	
	TIFFSetField(tiff_file,TIFFTAG_PHOTOMETRIC,1);
	TIFFSetField(tiff_file,TIFFTAG_COMPRESSION,1);
	
	TIFFSetField(tiff_file,TIFFTAG_IMAGELENGTH,dim_size[1]);
	TIFFSetField(tiff_file,TIFFTAG_IMAGEWIDTH,dim_size[0]);
	
	TIFFSetField(tiff_file,TIFFTAG_RESOLUTIONUNIT,1);
	TIFFSetField(tiff_file,TIFFTAG_XRESOLUTION,1);
	TIFFSetField(tiff_file,TIFFTAG_YRESOLUTION,1);
	
	TIFFSetField(tiff_file,TIFFTAG_ROWSPERSTRIP,1);
	TIFFSetField(tiff_file,TIFFTAG_ROWSPERSTRIP,1);	
	
	
	
}

@end
