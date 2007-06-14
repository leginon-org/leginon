#ifndef __MRC_H
#define __MRC_H

#ifdef __cplusplus
extern "C" {
#endif

// might be already define
// #define LITTLE_ENDIAN

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

typedef struct Imagic5HeadStructOld {
	int imn; // image location number (1,2,3,...)  
	int ifol; // number of images following (0,1,,...) important in first location  
	int ierror; //error code for this image during IMAGIC-5 run  
	int nhfr; //number of header records per image (=1 currently)  
	int nmonth; //creation month  
	int nday; //creation day  
	int nyear; //creation year  
	int nhour; //creation hour  
	int nminut; //creation minute  
	int nsec; //creation second 
	int npix2; //image size in BYTES as seen from the program (int(13)*int(89)) 
	int npixel; //total number of image elements  
	int ixlp; //number of lines per image (for 1D data IYLP1=1)  
	int iylp; //number of pixels per line 
	char type[4]; //4 characters determining the image type 
				//REAL: REAL/float 
				//INTG: INTEGER*2/short 
				//PACK: PACK/byte 
				//COMP: 2 REAL / 2 float 
				//RECO: complex format with 0 in imaginary part) 
	int ixold; //top left X co-ordinate before CUT-IMAGE (boxing)  
	int iyold; //top left Y co-ordinate before CUT-IMAGE (boxing) 
	float avdens; //average density in image  
	float sigma; //standard deviation of densities  
	float varian; //variance of densities in image  
	float oldavd; //old average density of this image  
	float densmax; //highest density in image  
	float densmin; //minimal density in image 
	int complex; //label indicating that data is always complex 
	float cxlength; //cell dimension in Angstr. (x-direction) (MRC(12))  
	float cylength; //cell dimension in Angstr. (y-direction) (MRC(11))  
	float czlength; //cell dimension in Angstr. (z-direction) (MRC(13))  
	float calpha; //cell angle alpha (MRC(14))  
	float cbeta; //cell angle beta (MRC(15))  
	char name[80]; //coded NAME/TITLE of the image (80 characters) 
	float CGAMMA; //cell angle gamma (MRC(16)) 
	int mapc; //axis corresponding to columns (MRC(17))  (1,2,3 for X,Y,Z)  
	int mapr; //axis corresponding to rows (MRC(18)) (1,2,3 for X,Y,Z)  
	int maps; //axis corresponding to sections (MRC(19)) (1,2,3 for X,Y,Z)  
	int ispg; //space group (MRC(23))
	int nxstart; //number of 1st column in map (def:0) (MRC(6)) (where map starts in columns)  
	int nystart; //number of 1st row in map (def:0) (MRC(5)) (where map starts in rows)  
	int nzstart; //number of 1st section in map (def:0) (MRC(7)) (where map starts in sections)  
	int nxintv; //number of intervals along X (MRC(9))  
	int nyintv; //number of intervals along Y (MRC(8))  
	int nzintv; //number of intervals along Z (MRC(10)) 
	int izlp; //number of 2D planes in 3D data (for 2D: IZLP1=1)  
	int i4lp; //number of 3D planes in 4D data (for 2D: I4LP1=1)  
	int i5lp;
	int i6lp;
	float alpha; //Euler angle alpha (3D and Angular Reconst.)  
	float beta; //Euler angle beta (3D and Angular Reconst.)  
	float gamma; //Euler angle gamma (3D and Angular Reconst.)  
	int imavers; //IMAGIC-5 version used (yyyymmdd) 
	int realtype; //floating point type, machine step 
				//16777216 for VAX/VMS 
				//33686018 for DEC/OSF, DEC/ULTRIX, LINUX, MS Windows 
				//67372036 for SiliconGraphics, SUN, HP, IBM 
	int buffering[28]; //Variables that control the buffering, don't change....
	int ronly; //flag in calling program to open file readonly (1: readonly) 
	float angle; //last rotation angle  
	float rcp; //rotational correlation peak  
	int ixpeak; //shift correlation peak in X direction  
	int iypeak; //shift correlation peak in Y direction  
	float ccc; //cross correlation peak hight  
	float errar; //error in angular reconstitution if -1.0: the file is a special file (FABOSA)  
	float err3d; //error in 3D reconstruction (TRUE-THREED)  
	int ref; //(multi-) reference number  
	float classno; //class number in classification  
	float locold; //location number before CUT-IMAGE (boxing) or copy in ANGULAR and EX-COPY  
	float oldavd2; //old average density (before NORM-VARIANCE, for example)  
	float oldsigma; //old sigma  
	float xshift; //last shift in X direction  
	float yshift; //last shift in Y direction  
	float numcls; //number of class members 
	float ovqual; //overall class quality if the image is a class average 
	float eangle; //equivalent angle  
	float exshift; //equivalent shift in X direction  
	float eyshift; //equivalent shift in Y direction  
	float cmtotvar; //used in MSA/IMAGECOOS  
	float informat; //Gauss norm / real*FT Space information of the data set  
	int numeigen; //number of eigen values in MSA  
	int niactive; //number of active images in MSA  
	float resolx; //Angstrom per pixel/voxel in X direction if float(105) = -1.0 (FABOSA): mm per pixel  
	float resoly; //Angstrom per pixel/voxel in Y direction  
	float resolz; //Angstrom per pixel/voxel in Z direction  
	float alpha2; //Euler angle alpha (from projection mapping)  
	float beta2; //Euler angle beta (from projection mapping)  
	float gamma2; //Euler angle gamma (from projection mapping)  
	float fabosa[3]; //Special FABOSA variables if float(105) = -1.0  
	float nmetric; //Metric used in MSA calculations  
	float actmsa; //a flag indicating whether the "image" is active or not. Used during MSA calculations  
	float coosmsa[69]; //COOSMSA  co-ordinates of "image" along factorial axis number 1 through 69 (maximum possible). 
	float eigval;  //eigenvalues if the "images" represent eigenimages (eigenvalue #1 into loc#1 etc.)  
	char history[228]; //coded history of image (228 characters)  
} Imagic5HeaderOld;

typedef struct Imagic5HeaderStruct {

		int imgnum;             // image number, [1,n]
		int count;              // total number of images - 1 (only first image), [0,n-1]
		int error;              // Error code for this image
		int headrec;            // # of header records/image (always 1)
		int mday;               // image creation time
		int month;
		int year;
		int hour;
		int minute;
		int sec;
		int reals;              // image size in reals
		int pixels;             // image size in pixels
		int ny;                 // # of lines / image
		int nx;                 // # of pixels / line
		char type[4];           // PACK, INTG, REAL, COMP, RECO
		int ixold;              // Top left X-coord. in image before windowing 
		int iyold;              // Top left Y-coord. in image before windowing 
		float avdens;           // average density
		float sigma;            // deviation of density
		float varia;            // variance of density
		float oldav;            // old average density
		float max;              // max density
		float min;              // min density
		int complex;            // not used
		float cellx;            // not used
		float celly;            // not used
		float cellz;            // not used
		float cella1;           // not used
		float cella2;           // not used
		char label[80];         // image id string
		int space[8];
		float mrc1[4];
		int mrc2;
		int space2[7];
		int lbuf;               // effective buffer len = nx
		int inn;                // lines in buffer = 1
		int iblp;               // buffer lines/image = ny
		int ifb;                // 1st line in buf = 0
		int lbr;                // last buf line read = -1
		int lbw;                // last buf line written = 0
		int lastlr;             // last line called for read = -1
		int lastlw;             // last line called for write = 1
		int ncflag;             // decode to complex = 0
		int num;                // file number = 40 (?)
		int nhalf;              // leff/2
		int ibsd;               // record size for r/w (words) = nx*2
		int ihfl;               // file # = 8
		int lcbr;               // lin count read buf = -1
		int lcbw;               // lin count wr buf = 1
		int imstr;              // calc stat on rd = -1
		int imstw;              // calc stat on wr = -1
		int istart;             // begin line in buf = 1
		int iend;               // end line in buf = nx
		int leff;               // eff line len = nx
		int linbuf;             // line len (16 bit) nx *2
		int ntotbuf;            // total buf in pgm = -1
		int space3[5];
		int icstart;            // complex line start = 1
		int icend;              // complex line end = nx/2
		int rdonly;             // read only = 0
		int misc[157];          // Remainder of header (EMAN1 specific settings not supported)
} Imagic5Header;

typedef struct Imagic5Struct {
	Imagic5Header *pHeaders;
	char *pbyData;
	unsigned int uCount;
} Imagic5;

typedef Imagic5 * Imagic5Ptr;
int loadImagic5(char *pszName, Imagic5 *pImagic5);
int loadImagic5Header(char *pszFilename, Imagic5Header *pHeader, int img_num);
int loadImagic5At(char *pszHedName, char *pszImgName, int img_num, Imagic5 *pImagic5);
void *readImagic5Images(FILE *pFImage, Imagic5 *pImagic5);
void *readImagic5ImagesAt(FILE *pFImage, int img_num, Imagic5 *pImagic5);
void freeImagic5(Imagic5 *pImagic5);

#ifdef __cplusplus
}
#endif

#endif

