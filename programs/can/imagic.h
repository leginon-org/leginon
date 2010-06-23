#ifndef IMAGICH
#define IMAGICH

struct imagicH {
int imnum;	// image number
int count;	// total # images in file (1st record only)
int error;
int headrec;	// # header records/image
int mday;
int month;
int year;
int hour;
int minute;
int sec;
int reals;	// image size in reals
int pixels;	// image size in pixels
int ny;
int nx;
char type[4];	// usu 'REAL', or 'INTG'
int ixold;
int iyold;
float avdens;	// average density
float sigma;	// deviation of density
float varia;	// variance
float oldav;	// old average dens
float max;	// max dens
float min;	// min dens
int complex;	// ?
float cellx;
float celly;
float cellz;
float cella1;
float cella2;
char label[80];	//30
int SPACE[8];	//50
float MRC1[4];	//58
int MRC2;	//62
int SPACE2[7];
int lbuf;		// effective buffer len = nx
int inn;		// lines in buffer = 1
int iblp;		// buffer lines/image = ny
int ifb;		// 1st line in buf = 0
int lbr;		// last buf line read = -1
int lbw;		// last buf line written = 0
int lastlr;		// last line called for read = -1
int lastlw;		// last line called for write = 1
int ncflag;		// decode to complex = 0
int num;		// file number = 40 (?)
int nhalf;		// leff/2
int ibsd;		// record size for r/w (words) = nx*2
int ihfl;		// file # = 8
int lcbr;		// lin count read buf = -1
int lcbw;		// lin count wr buf = 1
int imstr;		// calc stat on rd = -1
int imstw;		// calc stat on wr = -1
int istart;		// begin line in buf = 1
int iend;		// end line in buf = nx
int leff;		// eff line len	= nx
int linbuf;		// line len (16 bit) nx *2
int ntotbuf;	// total buf in pgm = -1
int SPACE3[5];
int icstart;	// complex line start = 1
int icend;		// complex line end = nx/2
int rdonly;		// read only = 0

int clsrep;		// EMAN specific, classes represented with 0x7a6b5c00 mask
int emanmisc[6];
float qual[50];	// quality info from EMAN classification
int cls[50];	// number of best class
int flags[50];	// eman flags
};

#endif
