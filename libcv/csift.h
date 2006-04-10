#include "defs.h"
#include "mutil.h"
#include "image.h"

typedef struct KeypointSt {
	float row, col, ori, scale;
	double A,B,C,D,E,F,maj,min,phi;
	int minr, maxr, minc, maxc;
	struct ImageSt *image;
} *Keypoint;

typedef struct DescriptorSt {
	float row, col, scale, ori;
	int descriptortype;
	int descriptorlength;
	float *descriptor;
} *Descriptor;

Keypoint EllipseToKeypoint( Ellipse e, Image im );
void KeypointsToDescriptors( PStack keypoints, PStack descriptors, int pb, int ob );
void DetermineMajorOrientations( Keypoint key, PStack keypoints, FStack orientations );
void PrintSIFTDescriptors( char *name, PStack descriptors );
float *CreateSIFTDescriptor( Image patch, int pb, int ob );
float *CreatePCADescriptor( Image patch );
void GenerateOrientationBins( Keypoint key, Image im, float *bins );
void KeypointToPatch( Keypoint key, Image patch );
Descriptor NewDescriptor( Keypoint key, int dlength, char dtype, float *d );
void OrientKeypointsAsClusters( PStack keypoints );
void GenerateClusterBins( Keypoint key, PStack keys, float *bins );
void FindMajorOrientations( PStack keys );
void PrintKeypoints( char *name, PStack keypoints );

void DrawDescriptor( Descriptor d, Image out );
void DrawKeypoint( Keypoint key, Image out, float ori );
void DrawOrientations( float *bins, Image out, float ori );
void DrawRegionInfo( MSERegion region, float t, Image out );
void PlotNeighborClusters( Keypoint key, PStack keys, Image out );
