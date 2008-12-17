#include "cvtypes.h"
#include "Array.h"
#include "MRC.h"
#include "PGM.h"
#include "Image.h"
#include "Ellipse.h"
#include "util.h"
#include "getopts.h"
#include "ctf.h"
#include "geometry.h"
#include <gsl/gsl_math.h>
#include <gsl/gsl_linalg.h>
#include <gsl/gsl_blas.h>
#include <gsl/gsl_eigen.h>
#include <gsl/gsl_multimin.h>

int main (int argc, char **argv) {
	
	srand((unsigned)time(NULL));
	
	struct options opts[] = {
		{ 1,	NULL,	"Pathname to CTF estimate file", 			   "ctf",	1 },
		{ 2,	NULL,	"Pathname to image file", 					   "img",	1 },
		{ 0,	NULL,	NULL,											NULL,	0 }
	};
	
	char arg[256];
	char imgpath[1024];
	char line[1024];
	s32 s_s = 0;
	
	ArrayP image = nil;
	
	f64 snr = 2.0;
	f64 df1 = 0.0;
	f64 df2 = 0.0;
	f64 dfr = 0.0;
	f64 ac = 0.07;
	f64 apix = 0.0;
	f64 cs = 0.0;
	f64 kv = 0.0;
	u32 binby = 2;
	
	f32 t0 = CPUTIME;	
	f32 t1 = CPUTIME;
	
	while ( ( s_s = getopts(argc,argv,opts,arg) ) != 0 ) {
		switch ( s_s ) {
			case -2:
				fprintf(stderr,"Argument %s is not understood\n",arg);
				return -1;
			case -1:
				fprintf(stderr,"No memory for parsing, exiting!!!\n");
				return -1;
			case  1:
				fprintf(stderr,"\nReading CTF Estimate File %s\n",arg);	
				FILE * fp = fopen(arg,"r");
				if ( fp == NULL ) return -1;
				
				while ( sscanf(fgets(line,1024,fp)," Final Params for image: %s",imgpath) != 1 );
				while ( sscanf(fgets(line,1024,fp)," Final Defocus: %le %le %le",&df1,&df2,&dfr) != 3 );
				while ( sscanf(fgets(line,1024,fp)," Amplitude Contrast: %le",&ac) != 1 );
				while ( sscanf(fgets(line,1024,fp)," Voltage: %le",&kv) != 1 );
				while ( sscanf(fgets(line,1024,fp)," Spherical Aberration: %le",&cs) != 1 );
				while ( sscanf(fgets(line,1024,fp)," Angstroms per pixel: %le",&apix) != 1 );
				
				fprintf(stderr,"\n");
				fprintf(stderr,"Image Path: %s\n",imgpath);
				fprintf(stderr,"APIX: %e KV: %e CS: %e\n",apix,kv,cs);
				fprintf(stderr,"DF1: %e DF2: %e DFR: %e\n",df1,df2,dfr);
				fprintf(stderr,"AMP: %e\n",ac);
				
				fclose(fp);
				break;
			case 2:
				image = [Array readMRCFile:arg];
				break;
			default:
				break;
		}
		
	}
	
	t1 = CPUTIME;
	fprintf(stderr,"\nReading image...");
	if ( image == nil ) image = [Array readMRCFile:imgpath];
	if ( image == nil ) return -1;
	[image setFlag:CV_ARRAY_DATA_SCALES to: TRUE];
	[image setTypeTo: TYPE_F64];
	fprintf(stderr,"\t\tDONE in %2.2f secs\n",CPUTIME-t1);
	
	t1 = CPUTIME;
	fprintf(stderr,"Performing FFT on image...");
	[image r2cfftc];
	fprintf(stderr,"\tDONE in %2.2f secs\n",CPUTIME-t1);
	
	u32 rows = [image sizeOfDimension:1];
	u32 cols = [image sizeOfDimension:0];
	u32 i, size = [image numberOfElements];
	
	t1 = CPUTIME;
	fprintf(stderr,"Creating synth CTF...");
	ArrayP ctf = g2DCTF(df2,df1,-dfr,rows,cols,apix,cs,kv,ac);
	fprintf(stderr,"\t\tDONE in %2.2f secs\n",CPUTIME-t1);
	
	f64 * cp = [ctf data];
	c64 * ip = [image data];
	
	u32 phase = 0;
	f64 wiener = 0.1;
	
	t1 = CPUTIME;
	fprintf(stderr,"Correcting image...");
	if (  phase ) for(i=0;i<size;i++) if ( -cp[i] < 0.0 ) ip[i] = -ip[i];
	if ( !phase ) for(i=0;i<size;i++) ip[i] = (-ip[i]*cp[i])/(cp[i]*cp[i]+wiener);
	fprintf(stderr,"\t\tDONE in %2.2f secs\n",CPUTIME-t1);
	
	t1 = CPUTIME;	
	fprintf(stderr,"Performing inverse fft...");
	[image c2rfftc];
	fprintf(stderr,"\tDONE in %2.2f secs\n",CPUTIME-t1);
		
	char name[1024];
	sprintf(name,"%s.corrected.mrc",basename([image name]));
	[image writeMRCFile:name];
	
	[image release];
	[ctf release];

	fprintf(stderr,"\t\t\t\tDONE in %2.2f secs\n",CPUTIME-t0);
		
}
