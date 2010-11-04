#include "MRC.h"

MRCHeaderP readMRCHeader( FILE *fp );
u32        writeMRCHeader( FILE *fp, MRCHeaderP header );

void       printMRCHeader( MRCHeaderP header );

u32        typeFromMRCType( u32 type );

void       printMRCHeader( MRCHeaderP header ) {
	fprintf(stderr,"nx %d ny %d nz %d\n",header->nx,header->ny,header->nz);
	fprintf(stderr,"mx %d my %d mz %d\n",header->mx,header->my,header->mz);
	fprintf(stderr,"lx %2.2f ly %2.2f lz %2.2f\n",header->x_length,header->y_length,header->z_length);
	fprintf(stderr,"sx %d sy %d sz %d\n",header->nxstart,header->nystart,header->nzstart);
	fprintf(stderr,"alpha %2.2f beta %2.2f gamma %2.2f\n",header->alpha,header->beta,header->gamma);
	fprintf(stderr,"mapc %d mapr %d maps %d\n",header->mapc,header->mapr,header->maps);
	fprintf(stderr,"Type %s\n",TYPE_STRINGS[typeFromMRCType(header->mode)]);
	fprintf(stderr,"amin %2.2f amax %2.2f amean %2.2f stdv %2.2f\n",header->amax,header->amin,header->amean,header->rms);
	fprintf(stderr,"xo %2.2f yo %2.2f zo %2.2f\n",header->xorigin,header->yorigin,header->zorigin);
	fprintf(stderr,"ispg %d nsymbt %d nlabl %d\n",header->ispg,header->nsymbt,header->nlabl);
}

u32        typeFromMRCType( u32 type ) {
	switch ( type ) {
		case MRC_MODE_BYTE:
		return TYPE_S08;
		case MRC_MODE_SHORT:
		return TYPE_S16;
		case MRC_MODE_FLOAT:
		return TYPE_F32;
		case MRC_MODE_SHORT_COMPLEX:
		return TYPE_NULL;
		case MRC_MODE_FLOAT_COMPLEX:
		return TYPE_C32;
		case MRC_MODE_UNSIGNED_SHORT:
		return TYPE_U16;
		default:
		return TYPE_NULL;
	}
}

u32        writeMRCHeader( FILE *fp, MRCHeaderP header ) {
	
	u32 count = 0;
	
	if ( !header || !fp ) return FALSE;

	u32 users = MRC_USERS;
	u32 label = MRC_LABEL_SIZE * MRC_NUM_LABELS;
	
	count += byteSwapWrite(fp, &header->nx,        1, 4 );
	count += byteSwapWrite(fp, &header->ny,        1, 4 );
	count += byteSwapWrite(fp, &header->nz,        1, 4 );
	count += byteSwapWrite(fp, &header->mode,      1, 4 );
	count += byteSwapWrite(fp, &header->nxstart,   1, 4 );
	count += byteSwapWrite(fp, &header->nystart,   1, 4 );
	count += byteSwapWrite(fp, &header->nzstart,   1, 4 );
	count += byteSwapWrite(fp, &header->mx,        1, 4 );
	count += byteSwapWrite(fp, &header->my,        1, 4 );
	count += byteSwapWrite(fp, &header->mz,        1, 4 );
	count += byteSwapWrite(fp, &header->x_length,  1, 4 ); 
	count += byteSwapWrite(fp, &header->y_length,  1, 4 );
	count += byteSwapWrite(fp, &header->z_length,  1, 4 );
	count += byteSwapWrite(fp, &header->alpha,     1, 4 );
	count += byteSwapWrite(fp, &header->beta,      1, 4 );
	count += byteSwapWrite(fp, &header->gamma,     1, 4 );
	count += byteSwapWrite(fp, &header->mapc,      1, 4 );
	count += byteSwapWrite(fp, &header->mapr,      1, 4 );
	count += byteSwapWrite(fp, &header->maps,      1, 4 );
	count += byteSwapWrite(fp, &header->amin,      1, 4 );
	count += byteSwapWrite(fp, &header->amax,      1, 4 );
	count += byteSwapWrite(fp, &header->amean,     1, 4 );
	count += byteSwapWrite(fp, &header->ispg,      1, 4 );
	count += byteSwapWrite(fp, &header->nsymbt,    1, 4 );
	count += byteSwapWrite(fp, &header->extra, users, 4 ); 
	count += byteSwapWrite(fp, &header->xorigin,   1, 4 );
	count += byteSwapWrite(fp, &header->yorigin,   1, 4 );
	count += byteSwapWrite(fp, &header->zorigin,   1, 4 );
	count += byteSwapWrite(fp, &header->map,	   1, 4 );
	count += byteSwapWrite(fp, &header->mach,	   1, 4 );
	count += byteSwapWrite(fp, &header->rms,       1, 4 );
	count += byteSwapWrite(fp, &header->nlabl,     1, 4 );
	count += byteSwapWrite(fp, &header->label, label, 1 );
	
	if ( count != MRC_COUNT ) return FALSE;
	else return TRUE;
	
}
 
MRCHeaderP readMRCHeader( FILE *fp ) {
	
	if ( fp == NULL ) return NULL;

	u32 users = MRC_USERS;
	u32 label = MRC_LABEL_SIZE * MRC_NUM_LABELS;
	u32 count = 0;
	
	MRCHeaderP header = malloc(sizeof(MRCHeaderSt));
	if ( header == NULL ) return NULL;
	
	count += byteSwapRead(fp, &header->nx,			1, 4 );
    count += byteSwapRead(fp, &header->ny,			1, 4 );
    count += byteSwapRead(fp, &header->nz,			1, 4 );
    count += byteSwapRead(fp, &header->mode,		1, 4 );
    count += byteSwapRead(fp, &header->nxstart,		1, 4 );
    count += byteSwapRead(fp, &header->nystart,		1, 4 );
    count += byteSwapRead(fp, &header->nzstart,		1, 4 );
    count += byteSwapRead(fp, &header->mx,			1, 4 );
    count += byteSwapRead(fp, &header->my,			1, 4 );
    count += byteSwapRead(fp, &header->mz,			1, 4 );
    count += byteSwapRead(fp, &header->x_length,	1, 4 ); 
    count += byteSwapRead(fp, &header->y_length,	1, 4 );
    count += byteSwapRead(fp, &header->z_length,	1, 4 );
    count += byteSwapRead(fp, &header->alpha,		1, 4 );
    count += byteSwapRead(fp, &header->beta,		1, 4 );
    count += byteSwapRead(fp, &header->gamma,		1, 4 );
    count += byteSwapRead(fp, &header->mapc,		1, 4 );
    count += byteSwapRead(fp, &header->mapr,		1, 4 );
    count += byteSwapRead(fp, &header->maps,		1, 4 );
    count += byteSwapRead(fp, &header->amin,		1, 4 );
    count += byteSwapRead(fp, &header->amax,		1, 4 );
    count += byteSwapRead(fp, &header->amean,		1, 4 );
    count += byteSwapRead(fp, &header->ispg,		1, 4 );
    count += byteSwapRead(fp, &header->nsymbt,		1, 4 );
    count += byteSwapRead(fp, &header->extra,	users, 4 );
    count += byteSwapRead(fp, &header->xorigin,		1, 4 );
    count += byteSwapRead(fp, &header->yorigin,		1, 4 );
 	count += byteSwapRead(fp, &header->zorigin,		1, 4 );
	count += byteSwapRead(fp, &header->map,			1, 4 );
	count += byteSwapRead(fp, &header->mach,		1, 4 );
	count += byteSwapRead(fp, &header->rms,			1, 4 );
    count += byteSwapRead(fp, &header->nlabl,		1, 4 );
    count += byteSwapRead(fp, &header->label,	label, 1 );
	
	if ( count != MRC_COUNT ) {
		free(header);
		return NULL;
	}

	return header;
	
}

@implementation Array ( MRC_File )
	
+ (ArrayP) readMRCFile: (char *)filename {
	
	FILE * fp = fopen(filename,"r");

	MRCHeaderP header = readMRCHeader( fp );
	
	if ( header == NULL ) goto error;

	u32 dims[4] = {header->nx,header->ny,header->nz-1,0};
	
	u32 type = typeFromMRCType( header->mode );
	
	if ( type == TYPE_NULL ) goto error;

	ArrayP image = [Array newWithType: type andDimensions: dims];
	
	u32   size = [image numberOfElements];
	u32  esize = [image elementSize];
	void *data = [image data];
	
	u32 count = byteSwapRead( fp, data, size, esize );
	
	if ( count != size ) goto error;
	
	[image setMinValue: header->amin];
	[image setMaxValue: header->amax];
	[image setMeanValue: header->amean];
	[image setStandardDeviation: header->rms];
	[image setFlag: CV_ARRAY_STATS_ARE_VALID to: TRUE];
	[image setNameTo: filename];
	
	free(header);

	return image;
	
	error:
	fprintf(stderr,"Reading MRC image %s failed!!\n",filename);
	
	if ( fp != NULL ) fclose(fp);
	if ( header != NULL ) free(header);
	if ( image != nil ) [image release];
	
	return nil;
	
}

- (u32)    writeMRCFile: (char *)filename {

	FILE * fp = fopen(filename,"wb");
	MRCHeaderP header = NEW(MRCHeaderSt);
	void * outdata = NULL;
	
	if ( fp == NULL ) goto error;
	if ( header == NULL ) goto error;
	
	header->nx       	= [self sizeOfDimension: 0];
	header->ny       	= [self sizeOfDimension: 1];
	header->nz       	= [self sizeOfDimension: 2];
	header->mx       	= header->nx;
	header->my       	= header->ny;
	header->mz       	= header->nz;
	header->x_length 	= header->nx;
	header->y_length 	= header->ny;
	header->z_length 	= header->nz;
	header->nxstart  	= 0;
	header->nystart  	= 0;
	header->nzstart  	= 0;
	header->mapc     	= 1;
	header->mapr     	= 2;
	header->maps     	= 3;
	header->alpha    	= 90;
	header->beta     	= 90;
	header->gamma    	= 90;
	header->amean    	= [self meanValue];
	header->amax     	= [self maxValue];
	header->amin     	= [self minValue];
	header->rms    		= [self standardDeviation];
	header->mach		= time(NULL);
	// "MAP " from ascii to little-endian integer:  
	//   ord('M')=77, ord('A')=65, ord('P')=80, ord(' ')=32
	//   reverse order and powers of 256
	//   32*(256**3) + 80*(256**2) + 65*(256) + 77
	header->map			= 542130509;
	header->xorigin		= header->x_length / 2;
	header->yorigin		= header->y_length / 2;
	header->zorigin		= header->z_length / 2;
	header->ispg   		= 0;
	header->nsymbt		= 0;
	header->nlabl		= 0;
	
	if ( header->nz == 0 ) header->nz = 1; 

	u32 k;
	for(k=0;k<MRC_USERS;k++) header->extra[k] = 0;
	for(k=0;k<MRC_NUM_LABELS;k++) header->label[k][0] = '\0';
	
	u32 element_size = 0;

	switch ( type ) {
		case TYPE_U08:
			outdata = [self dataAsType: TYPE_U08 withFlags:CV_COPY_DATA|CV_MAINTAIN_PRECISION];
			element_size = sizeFromType(TYPE_U08);
			header->mode = MRC_MODE_BYTE;
			break;
		case TYPE_S08:
		case TYPE_S16:
			outdata = [self dataAsType: TYPE_S16 withFlags:CV_COPY_DATA|CV_MAINTAIN_PRECISION];
			element_size = sizeFromType(TYPE_S16);
			header->mode = MRC_MODE_SHORT;
			break;
		case TYPE_U16:
			outdata = [self dataAsType: TYPE_U16 withFlags:CV_COPY_DATA|CV_MAINTAIN_PRECISION];
			element_size = sizeFromType(TYPE_U16);
			header->mode = MRC_MODE_UNSIGNED_SHORT;
			break;
		case TYPE_S32:
		case TYPE_U32:
		case TYPE_S64:
		case TYPE_U64:
		case TYPE_F32:
		case TYPE_F64:
			outdata = [self dataAsType: TYPE_F32 withFlags:CV_COPY_DATA|CV_MAINTAIN_PRECISION];
			element_size = sizeFromType(TYPE_F32);
			header->mode = MRC_MODE_FLOAT;
			break;
		case TYPE_C32:
		case TYPE_C64:
			outdata = [self dataAsType: TYPE_C32 withFlags:CV_COPY_DATA];
			element_size = sizeFromType(TYPE_C32);
			header->mode = MRC_MODE_FLOAT_COMPLEX;
			break;
		default:
			goto error;
	}

	if ( outdata == NULL ) goto error;
	if ( writeMRCHeader(fp,header) == FALSE ) goto error;
	
	u32 count = byteSwapWrite( fp, outdata, size, element_size );
	
	if ( count != size ) goto error;
	
	free(header);
	free(outdata);
	fclose(fp);

	return TRUE;
	
	error:
	
	if ( fp != NULL ) fclose(fp);
	if ( header != NULL ) free(header);
	if ( outdata != NULL ) free(outdata);
	return FALSE;
	
}

@end
