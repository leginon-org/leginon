
#ifndef libCV_mser
#define libCV_mser

typedef struct MSERArraySt {
	struct ImageSt *image;
	int maxv, minv, rows, cols, size;
	int *sp, *sb, maxbin;
	int *roots, *sizes, *tvals;
	void **regions;
	char *flags;	
} *MSERArray;

void TrackRegions( MSERArray pa, PStack regions, int minsize, int maxsize, int minperiod, float minstable );
void DetermineStableRegions( MSERArray pa, PStack regions, int ud, int minPeriod, float minStable );
void FindStablePeriods( PointStack sizes, FStack sp, int minPeriod, float minStable );
int JoinNeighbors( int *sp, int *roots, int *sizes, int *tvals, char *flags, int stride, int k, int kmin, int kmax, int *idle, int idlesize, int minsize, int maxsize );
int JoinNeighborsUp( int *sp, int *roots, int *sizes, int *tvals, char *flags, int stride, int k, int kmin, int kmax, int *idle, int idlesize, int minsize, int maxsize );
int JoinNeighborsDown( int *sp, int *roots, int *sizes, int *tvals, char *flags, int stride, int k, int kmin, int kmax, int *idle, int idlesize, int minsize, int maxsize );
int ProcessTouchedRoots( int *roots, int *sizes, char *flags, void **regions, int *idle, int idlesize, int tic );
void CarveOutRegionUp( int root, Image image, PointStack borderpixels, float t );
int SearchHoodUp( int row, int col, int **p, int t1, float t, int maxrow, int maxcol );
int SearchHoodDown( int row, int col, int **p, int t1, float t, int maxrow, int maxcol );
void CarveOutRegionDown( int root, Image image, PointStack borderpixels, float t );

void ResetMSERArray( MSERArray pa );
MSERArray FreeMSERArray( MSERArray pa );
MSERArray ImageToMSERArray( Image image );
char MSERArrayGood( MSERArray array );

void DrawConnectedRegions( MSERArray ma );

#endif
