#ifndef __MRC_H
#define __MRC_H

/*  might be already define */
/*  #define LITTLE_ENDIAN */

#ifdef LITTLE_ENDIAN
#define LITTLE_ENDIAN_HOST 1
#define BIG_ENDIAN_HOST 0
#else
#define BIG_ENDIAN_HOST 1
#define LITTLE_ENDIAN_HOST 0
#endif

#define LITTLE_ENDIAN_DATA 0
#define BIG_ENDIAN_DATA 1

#define MRC_HEADER_SIZE		1024
#define MRC_MODE_BYTE           0
#define MRC_MODE_SHORT          1
#define MRC_MODE_FLOAT          2
#define MRC_MODE_SHORT_COMPLEX  3
#define MRC_MODE_FLOAT_COMPLEX  4
#define MRC_MODE_UNSIGNED_SHORT 6

#define MRC_USER            25
#define MRC_LABEL_SIZE      80
#define MRC_NUM_LABELS      10

#include <stdio.h>

typedef struct MRCHeaderStruct {
	int			nx;		/* Number of columns */
	int			ny;		/* Number of rows */
	int			nz;		/* Number of sections */
	int			mode;		/* See modes above. */
	int			nxstart;	/* No. of first column in map   default 0.*/
	int			nystart;	/* No. of first row in map  default 0.*/
	int			nzstart;	/* No. of first section in map  default 0.*/
	int			mx;		/* Number of intervals along X. */
	int			my;		/* Number of intervals along Y. */
	int			mz;		/* Number of intervals along Z. */
	float			x_length;	/* Cell dimensions (Angstroms). */
	float			y_length;	/* Cell dimensions (Angstroms). */
	float			z_length;	/* Cell dimensions (Angstroms). */
	float			alpha;		/* Cell angles (Degrees). */
	float			beta;		/* Cell angles (Degrees). */
	float			gamma;		/* Cell angles (Degrees). */
	int			mapc;		/* Which axis corresponds to Columns.  */
	int			mapr;		/* Which axis corresponds to Rows. */
	int			maps;		/* Which axis corresponds to Sections. */
	float			amin;		/* Minimum density value. */
	float			amax;		/* Maximum density value. */
	float			amean;		/* Mean density value.*/
	int			ispg;		/* Space group number (0 for images) */
	int			nsymbt;		/* Number of bytes used for storing symmetry operators */
	unsigned long	extra[MRC_USER];	/* For user, all set to zero by default */
	float			xorigin;	/* X origin */
	float			yorigin;	/* Y origin */
	float			zorigin;	/* Z origin */
	char			map[4];		/* character string 'MAP ' to identify file type */
	char			machstamp[4];	/* machine stamp */
	float			rms;		/* rms deviation of map from mean density*/
	int			nlabl;		/* Number of labels being used. */
	/* 10 text labels of 80 characters each. */
	char			label[MRC_NUM_LABELS][MRC_LABEL_SIZE + 1];
} MRCHeader;

typedef struct MRCStruct {
	MRCHeader header;
	char *pbyData;
} MRC;

typedef MRC * MRCPtr;

int loadMRC(char *pszFilename, MRC *pMRC);
int loadMRCHeader(char *pszFilename, MRCHeader *pMRCHeader);
int readMRCHeader(FILE *pFMRC, MRCHeader *pMRCHeader);

#define SIZEOF_I5_HEADER_ENTRY 4
#define NUM_I5_HEADER_ENTRIES 256
#define SIZEOF_I5_HEADER SIZEOF_I5_HEADER_ENTRY * NUM_I5_HEADER_ENTRIES

typedef struct Imagic5HeaderStruct {

		int imgnum;             /*  image number, [1,n] */
		int count;              /*  total number of images - 1 (only first image), [0,n-1] */
		int error;              /*  Error code for this image */
		int headrec;            /*  # of header records/image (always 1) */
		int mday;               /*  image creation time */
		int month;
		int year;
		int hour;
		int minute;
		int sec;
		int reals;              /*  image size in reals */
		int pixels;             /*  image size in pixels */
		int ny;                 /*  # of lines / image */
		int nx;                 /*  # of pixels / line */
		char type[4];           /*  PACK, INTG, REAL, COMP, RECO */
		int ixold;              /*  Top left X-coord. in image before windowing  */
		int iyold;              /*  Top left Y-coord. in image before windowing  */
		float avdens;           /*  average density */
		float sigma;            /*  deviation of density */
		float varia;            /*  variance of density */
		float oldav;            /*  old average density */
		float max;              /*  max density */
		float min;              /*  min density */
		int complex;            /*  not used */
		float cellx;            /*  not used */
		float celly;            /*  not used */
		float cellz;            /*  not used */
		float cella1;           /*  not used */
		float cella2;           /*  not used */
		char label[80];         /*  image id string */
		int space[8];
		float mrc1[4];
		int mrc2;
		int space2[7];
		int lbuf;               /*  effective buffer len = nx */
		int inn;                /*  lines in buffer = 1 */
		int iblp;               /*  buffer lines/image = ny */
		int ifb;                /*  1st line in buf = 0 */
		int lbr;                /*  last buf line read = -1 */
		int lbw;                /*  last buf line written = 0 */
		int lastlr;             /*  last line called for read = -1 */
		int lastlw;             /*  last line called for write = 1 */
		int ncflag;             /*  decode to complex = 0 */
		int num;                /*  file number = 40 (?) */
		int nhalf;              /*  leff/2 */
		int ibsd;               /*  record size for r/w (words) = nx*2 */
		int ihfl;               /*  file # = 8 */
		int lcbr;               /*  lin count read buf = -1 */
		int lcbw;               /*  lin count wr buf = 1 */
		int imstr;              /*  calc stat on rd = -1 */
		int imstw;              /*  calc stat on wr = -1 */
		int istart;             /*  begin line in buf = 1 */
		int iend;               /*  end line in buf = nx */
		int leff;               /*  eff line len = nx */
		int linbuf;             /*  line len (16 bit) nx *2 */
		int ntotbuf;            /*  total buf in pgm = -1 */
		int space3[5];
		int icstart;            /*  complex line start = 1 */
		int icend;              /*  complex line end = nx/2 */
		int rdonly;             /*  read only = 0 */
		int misc[157];          /*  Remainder of header (EMAN1 specific settings not supported) */
} Imagic5Header;

typedef struct Imagic5Struct {
	Imagic5Header *pHeaders;
	char *pbyData;
	unsigned int uCount;
} Imagic5;

typedef Imagic5 * Imagic5Ptr;

typedef struct Imagic5oneStruct {
	Imagic5Header header;
	char *pbyData;
} Imagic5one;

typedef Imagic5one * Imagic5onePtr;

int loadImagic5(char *pszName, Imagic5 *pImagic5);
int loadImagic5Header(char *pszFilename, Imagic5Header *pHeader, int img_num);
int loadImagic5At(char *pszHedName, char *pszImgName, int img_num, Imagic5one *pImagic5);
int readImagic5Header(FILE *pFHeader, Imagic5Header *pHeader, int img_num);
void *readImagic5Images(FILE *pFImage, Imagic5 *pImagic5);
void *readImagic5ImagesAt(FILE *pFImage, int img_num, Imagic5one *pImagic5);
void freeImagic5(Imagic5 *pImagic5);
void freeImagic5one(Imagic5one *pImagic5);

#define NUM_SPIDER_HEADER_ENTRIES 256

typedef struct SpiderHeaderStruct {
	float nslice;           /*  number of slices in volume; 1 for a 2D image. */
	float nrow;         /*  nrow, number of rows per slice  */
	float irec;                     /*  total number of records in the file (unused) */
	float nhistrec;     /*  obsolete, unused */

	float type;             /* iform, file type */

	float mmvalid;          /*  imami, max/min flag. */
	float max;          /*  fmax, max value */
	float min;          /*  fmin, min value */
	float mean;         /*  av, average value */
	float sigma;            /*  sig, std dev, -1=unknown */
	float ihist;        /*  obsolete, no longer used */
	float nsam;         /*  nsam, number of pixels per row */
	float headrec;          /*  labrec, number of records in header */
	float angvalid;         /*  iangle, flag, 1 if tilt angles have been computed */
	float phi;          /*  tilt angle */
	float theta;        /*  tilt angle */
	float gamma;        /*  tilt angle  (also called psi). */
	float dx;           /*  xoff, x translation */
	float dy;           /*  yoff, y translation */
	float dz;                       /*  zoff, z translation */
	float scale;        /*  scale factor */
	float headlen;          /*  labbyt, header length in bytes */
	float reclen;       /*  lenbyt, record length in bytes */

	float istack;
	float inuse;        /*  not used */
	float maxim;
	float imgnum;

	float lastindx;    

	float u6;          /*  unused */
	float u7;          /*  unused */

	float Kangle;   
	float phi1;
	float theta1;
	float psi1;
	float phi2;
	float theta2;
	float psi2;
	char  u8[48];       /* unused */
	float xf[27];       /*  reserved for Jose Maria's transforms */
	float u9[135];      /*  unused */
	char date[11];      /*  creation date e.g. 27-MAY-1999  */
	char time[8];       /*  creation time e.g. 09:43:19  */
	char title[160];    
} SpiderHeader;

typedef struct SpiderStruct {
	SpiderHeader header;
	char *pbyData;
} Spider;

typedef Spider * SpiderPtr;

int readSpiderHeader(FILE *pFSpider, SpiderHeader *pSpiderh);
int loadSpiderHeader(char *pszFilename, SpiderHeader *pSpiderh, int img_num);
int readSpiderAt(FILE *imgstream, int img_num, Spider *pSpider);
int loadSpiderAt(char *pszImgName, int img_num, Spider *pSpider);

#ifdef __cplusplus
}
#endif

#endif

