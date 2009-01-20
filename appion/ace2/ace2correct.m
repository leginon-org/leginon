#include "cvtypes.h"
#include "Array.h"
#include "MRC.h"
#include "PGM.h"
#include "Image.h"
#include "util.h"
#include "getopts.h"
#include "ctf.h"

#define CORRECT_PHASE					( 1<<0 )
#define CORRECT_WIENER					( 1<<1 )
#define CORRECT_BACKGROUND				( 1<<2 )
#define CORRECT_ENVELOPE				( 1<<3 )

typedef struct CTFParamsSt {
	
	char img_path[1024];
	f64 kv;
	f64 cs;
	f64 apix;
	f64 defocus_x;
	f64 defocus_y;
	f64 astig_angle;
	f64 amp_c;
	
	u08 correction_type;
	f64 wiener;

//	char * background_path;
//	char * envelope_path;
//	f64 * explicit_background_1d;
//	f64 * explicit_background_2d;
//	f64 * explicit_envelope_1d;
//	f64 * explicit_envelope_2d;
//	f64 * model_background_1d;
//	f64 * model_background_2d;
//	f64 * model_envelope_1d;
//	f64 * model_envelope_2d;
	
//	f64 (*background_function_1d)(f64 *,f64);
//	f64 (*background_function_2d)(f64 *,f64);
//	f64 (*envelope_function_1d)(f64 *,f64);
//	f64 (*envelope_function_2d)(f64 *,f64);
	
} CTFParamsSt;

typedef CTFParamsSt * CTFParams;

CTFParams newCTFParams() {
	
	CTFParams c = malloc(sizeof(CTFParamsSt));
	if ( c == NULL ) return c;
	
	c->kv = 120.0;
	c->cs = 2.0;
	c->apix = 1.55;
	c->defocus_x = 0.0;
	c->defocus_y = 0.0;
	c->astig_angle = 0.0;
	c->amp_c = 0.2;
	
	c->correction_type = CORRECT_PHASE;
	c->wiener = 0.15;
	
	return c;
	
}

u32 parseACE2CTFFile( char path[], CTFParams c ) {
	
	if ( path == NULL ) {
		fprintf(stderr,"ERROR: Pathname is NULL\n");
		exit(1);
	}
	
	if ( c == NULL ) {
		fprintf(stderr,"ERROR: CTFParams is NULL\n");
		exit(1);
	}
	
	FILE * fp = fopen(path,"r");
	if ( fp == NULL ) {
		fprintf(stderr,"ERROR: Could not open ACE2 CTF File: %s\n",path);
		return 0;
	}
	
	u32 max_line_length = 1024;
	char line[max_line_length];
	
	u32 count = 0;
	
	while ( fgets(line,max_line_length,fp) != NULL ) {
		
		count += sscanf(line," Final Params for image: %s",c->img_path);
		count += sscanf(line," Final Defocus: %le %le %le",&(c->defocus_x),&(c->defocus_y),&(c->astig_angle));
		count += sscanf(line," Amplitude Contrast: %le",&(c->amp_c));
		count += sscanf(line," Voltage: %le",&(c->kv));
	 	count += sscanf(line," Spherical Aberration: %le",&(c->cs));
		count += sscanf(line," Angstroms per pixel: %le",&(c->apix));
		
	}
	
	fclose(fp);
	
	return count;
	
}

CTFParams parseACE2CorrectOptions( int argc, char **argv ) {
	
	CTFParams ctfp = newCTFParams();
	
	if ( ctfp == NULL ) {
		fprintf(stderr,"ERROR: Could not allocate needed memory during option parsing\n");
		exit(-1);
	}
	
	struct options opts[] = {
		{ 1,	NULL,	"Path to CTF estimate file",	 			   "ctf",	1 },
		{ 2,	NULL,	"Path to image file",	 					   "img",	1 },
		{ 3,	NULL,	"Microscope voltage in kilovolts",				"kv",	1 },
		{ 4,	NULL,	"Microscope Spherical Aberration in mm",		"cs",	1 },
		{ 5,	NULL,	"Angstroms per pixel",						  "apix",	1 },
		{ 6,	NULL,	"Defocus: x,y,angle in um,um,radians",			"df",	1 },
		{ 7,	NULL,	"Correct only phase signs",	  		  		 "phase",	0 },
		{ 8,	NULL,	"Correct using wiener filter",		 	    "wiener",	1 },		
		{ 0,	NULL,	NULL,											NULL,	0 }
	};
	
	u32 option = 0;
	char arg[1024];
	
	while ( ( option = getopts(argc,argv,opts,arg) ) != 0 ) {
		switch ( option ) {
			case -1:
				fprintf(stderr,"No memory for parsing, exiting!!!\n");
				exit(-1);
			case  1:
				if ( parseACE2CTFFile(arg,ctfp) != 8 ) fprintf(stderr,"!!!! Incomplete ACE2 CTF File !!!!\n");
				break;
			case 2:
				strcpy(ctfp->img_path,arg);
				break;
			case 3:
				sscanf(arg,"%le",&(ctfp->kv));
				break;
			case 4:
				sscanf(arg,"%le",&(ctfp->cs));
				break;
			case 5:
				sscanf(arg,"%le",&(ctfp->apix));
				break;
			case 6:
				sscanf(arg,"%le,%le,%le",&(ctfp->defocus_x),&(ctfp->defocus_y),&(ctfp->astig_angle));
				break;
			case 7:
				ctfp->correction_type |= CORRECT_PHASE;
				ctfp->correction_type &= !CORRECT_WIENER;
				break;
			case 8:
				ctfp->correction_type &= !CORRECT_PHASE;
				ctfp->correction_type |= CORRECT_WIENER;
				sscanf(arg,"%le",&(ctfp->wiener));
				break;
			default:
				break;
		}
		
	}
	
	return ctfp;
	
}

void printFinalCTFParams( CTFParams p, char path[] ) {
	
	if ( p == NULL || path == NULL ) return;
	
	FILE * fp = NULL;
	
	if ( strcmp(path,"stdout") ) fp = stdout;
	else if ( strcmp(path,"stderr") ) fp = stderr;
	else fp = fopen(path,"w");
	
	if ( fp == NULL ) return;
	
	fprintf(fp,"Image Path: %s\n",p->img_path);
	fprintf(fp,"APIX: %le KV: %le CS(mm): %le\n",p->apix,p->kv,p->cs);
	fprintf(fp,"Defocus(X): %le Defocus(Y): %le Astigmatism Angle: %le\n",p->defocus_x,p->defocus_y,p->astig_angle);
	fprintf(fp,"Amplitude Contrast: %le\n",p->amp_c);
	
	fclose(fp);
	
}

int main (int argc, char **argv) {
	COMPILE_INFO;

	srand((unsigned)time(NULL));
	
	CTFParams ctfp = parseACE2CorrectOptions(argc,argv);

	if ( ctfp == NULL ) {
		fprintf(stderr,"ERROR: Parameters could not be set\n");
		exit(-1);
	}
	
	ArrayP image = nil;
	
	fprintf(stderr,"\nFinal Parameters being used for correction:\n");
	printFinalCTFParams(ctfp,"stderr");
	fprintf(stderr,"\n");
	
	u32 cty = ctfp->correction_type;
	f64 snr = ctfp->wiener;
	f64 df1 = ctfp->defocus_x;
	f64 df2 = ctfp->defocus_y;
	f64 dfr = ctfp->astig_angle;
	f64 ac 	= ctfp->amp_c;
	f64 apix = ctfp->apix;
	f64 cs = ctfp->cs;
	f64 kv = ctfp->kv;
	
	f32 t0 = CPUTIME;	
	f32 t1 = CPUTIME;

//---------Read image and convert to proper format----------------------------------------------

	t1 = CPUTIME;
	
	fprintf(stderr,"\nReading image...");
	
	if ( image == nil ) image = [Array readMRCFile:ctfp->img_path];
	if ( image == nil ) {
		fprintf(stderr,"ERROR: Could not read image\n");
		exit(-1);
	}
	
	[image setFlag:CV_ARRAY_DATA_SCALES to: TRUE];
	[image setTypeTo: TYPE_F64];
	
	fprintf(stderr,"\t\t\tDONE in %2.2f secs\n",CPUTIME-t1);

//---------Create CTF of image using fftw r2c transform----------------------------------------

	t1 = CPUTIME;
	fprintf(stderr,"Performing FFT on image...");
	[image r2cfftc];
	fprintf(stderr,"\t\tDONE in %2.2f secs\n",CPUTIME-t1);

//---------Create synthetic CTF for correction-------------------------------------------------
	
	t1 = CPUTIME;
	fprintf(stderr,"Creating synth CTF...");
	
	u32 rows = [image sizeOfDimension:1];
	u32 cols = [image sizeOfDimension:0];

	ArrayP ctf = g2DCTF(df2,df1,-dfr,rows,cols,apix,cs,kv,ac);
	
	fprintf(stderr,"\t\t\tDONE in %2.2f secs\n",CPUTIME-t1);
	
//---------Correct CTF of image----------------------------------------------------------------	
	
	f64 * cp = [ctf data];
	c64 * ip = [image data];
	u32 i, size = [image numberOfElements];
		
	t1 = CPUTIME;
	
	if ( cty & CORRECT_PHASE ) {
		fprintf(stderr,"Correcting image using phase flips...");
		for(i=0;i<size;i++) if ( -cp[i] < 0.0 ) ip[i] = -ip[i];
	}
	if ( cty & CORRECT_WIENER ) {
		fprintf(stderr,"Correcting image using wiener filter...");
		for(i=0;i<size;i++) ip[i] = (-ip[i]*cp[i])/(cp[i]*cp[i]+snr);
	}
	
	fprintf(stderr,"\tDONE in %2.2f secs\n",CPUTIME-t1);
	
//---------Perform inverse FFT using FFTW c2r transform-----------------------------------------		
	
	t1 = CPUTIME;	
	fprintf(stderr,"Performing inverse fft...");
	
	[image c2rfftc];
	
	fprintf(stderr,"\t\tDONE in %2.2f secs\n",CPUTIME-t1);
	
//---------Writing corrected image--------------------------------------------------------------		
	
	char name[1024];
	sprintf(name,"%s.corrected.mrc",basename([image name]));
	[image writeMRCFile:name];
	
	[image release];
	[ctf release];

	fprintf(stderr,"\nTotal Correction Time: %2.2f secs\n",CPUTIME-t0);
		
}
