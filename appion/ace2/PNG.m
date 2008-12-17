#include "PNG.h"

@implementation Array ( PNG_File )

+(ArrayP) readPNGFile:(char *)filename {
	fprintf(stderr,"PNG File reading not supported at this time\n");
	return nil;
}

-(u32) writePNGFile:(char *)filename {
	
	FILE * fp = NULL;
	png_structp png_image = NULL;
	png_infop png_image_info = NULL;
	void * outdata = NULL;
	
//	if ( ndim != 2 ) goto error;
	
	fp = fopen(filename, "wb");
//	if ( fp == NULL ) goto error;
	
	png_image = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
//	if ( png_image == NULL ) goto error;
	
	png_image_info = png_create_info_struct(png_image);
//	if ( png_image_info == NULL ) goto error;

//	if (setjmp(png_jmpbuf(png_image))) goto error;
	setjmp(png_jmpbuf(png_image));
	
	png_init_io(png_image, fp);
	
	u32 rows = dim_size[1];
	u32 cols = dim_size[0];
	u32 bit_depth = 0;
	
	switch ( type ) {
		case TYPE_S08:
		case TYPE_U08:
			outdata = [self dataAsType: TYPE_U08 withFlags:CV_COPY_DATA|CV_MAINTAIN_PRECISION];
			bit_depth = 8;
			break;
		case TYPE_S16:
		case TYPE_U16:
		case TYPE_S32:
		case TYPE_U32:
		case TYPE_S64:
		case TYPE_U64:
		case TYPE_F32:
		case TYPE_F64:
			fprintf(stderr,"Writing PNG as 16-bit gray image\n");
			
			outdata = [self dataAsType: TYPE_U16 withFlags:CV_COPY_DATA|CV_MAINTAIN_PRECISION];
			bit_depth = 16;
			break;
		case TYPE_C32:
		case TYPE_C64:
//			outdata = [self dataAsType: TYPE_U16 withFlags:CV_COPY_DATA];
//			bit_depth = 16;
			break;
//		default:
//			goto error;
	}

	png_set_IHDR(png_image, png_image_info, cols, rows, bit_depth, PNG_COLOR_TYPE_GRAY, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
	if (bit_depth > 8) png_set_swap(png_image);
	png_byte * image_rows[rows];
	int r; for(r=0;r<rows;r++) image_rows[r] = outdata + cols*r*2;
	png_set_rows(png_image, png_image_info, image_rows);
	
	png_write_png(png_image, png_image_info, PNG_TRANSFORM_IDENTITY, NULL);
	
	png_destroy_write_struct(&png_image, &png_image_info);
	free(outdata);
	fclose(fp);
	
	return 1;
/*	
	error:
	
	if ( fp != NULL ) fclose(fp);
	if ( png_image != NULL && png_image_info != NULL ) png_destroy_write_struct(&png_image, &png_image_info);
	if ( outdata != NULL ) free(outdata);
	return 0;
*/	
}

@end