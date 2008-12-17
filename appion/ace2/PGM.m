#include "PGM.h"

void  skipComments( FILE *fp ) ;

void  skipComments( FILE *fp ) {
    u32 ch;
    ch = fscanf(fp," ");      
	while ((ch = fgetc(fp)) == '#') {
		while ((ch = fgetc(fp)) != '\n'  &&  ch != EOF);
		ch = fscanf(fp," ");
    }
    ungetc(ch, fp);
}

@implementation Array ( PGM_File )

+ (ArrayP) readPGMFile: (char *)filename {
	
	FILE *fp = fopen (filename, "r");
    
	if ( fp == NULL ) goto error;
	
	u32 c1, c2, c3, c4, c5, rows, cols, max, k;

	c1 = fgetc(fp);
	c2 = fgetc(fp);
	skipComments(fp);
	c3 = fscanf(fp,"%d",&cols);
	skipComments(fp);
	c4 = fscanf(fp,"%d",&rows);
	skipComments(fp);
	c5 = fscanf(fp,"%d",&max);
  
	if (c1 != 'P' || c2 != '5' || c3 != 1 || c4 != 1 || c5 != 1 || max > 255) goto error;
	
	fgetc(fp); 

	fprintf(stderr,"creating array...");
	
	u32 dims[3] = {cols,rows,0};
	ArrayP image = [Array newWithType:TYPE_U08 andDimensions:dims];
	if ( image == nil || [image data] == NULL ) goto error;
	
	skipComments(fp);
	fread([image data],sizeFromType(TYPE_U08),[image numberOfElements],fp);
	[image setNameTo: filename];
	
	fclose(fp);
	
	return image;
	
	error:
	if ( fp != NULL ) fclose(fp);
	if ( image != nil ) [image release];
	return nil;
	
}

- (u32)    writePGMFile: (char *)filename {
	
	u32 rows = [self sizeOfDimension:1];
	u32 cols = [self sizeOfDimension:0];

	u32 k;
	u08 * outdata = [self dataAsType: TYPE_U08 withFlags:CV_COPY_DATA|CV_MAINTAIN_PRECISION];
	FILE *fp = fopen(filename, "wb");
	
	if ( outdata == NULL || fp == NULL ) goto error;
	
    fprintf(fp, "P5\n%d %d\n255\n", cols, rows );
	
	for (k=0;k<size;k++) fputc(outdata[k],fp);
	
	free(outdata);
	fclose(fp);
	
	return TRUE;
	
	error:
	if ( fp != NULL ) fclose(fp);
	if ( outdata != NULL ) free(outdata);
	return FALSE;
	
}

@end

