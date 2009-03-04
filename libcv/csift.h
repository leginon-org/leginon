
#ifndef libCV_csift
#define libCV_csift

#include "mser.h"
#include "mutil.h"
#include "image.h"

typedef struct DescriptorSt {
	float row, col, scale, ori;
	int descriptortype;
	int descriptorlength;
	float *descriptor;
} *Descriptor;

void RegionsToSIFTDescriptors( PStack regions, PStack descriptors, int pb, int ob, int psize );
void RegionToPatch( Region key, Image source, Image patch, float scale );
void PatchToMags( Image patch, FArray mags, FArray oris );
Descriptor NewDescriptor( Region key, int dlength, char dtype, float *d );
float *SIFTDescriptorFromPatch( FArray mags, FArray oris, float ori, int pb, int ob );
float *GLOHDescriptorFromPatch( Image patch, int pb, int ob );
void PrintSIFTDescriptors( char *name, PStack descriptors );
float *PCADescriptorFromPatch( Image patch );
void PrintRegions( char *name, PStack Regions );
void DrawRegion( Region key, float scale );
void freeDescriptors( PStack desc );
void freeRegions( PStack desc );
void freeDescriptor( Descriptor desc );

#endif
