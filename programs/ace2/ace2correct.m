#include "cvtypes.h"
#include "Array.h"
#include "MRC.h"
#include "PGM.h"
#include "Image.h"
#include "util.h"
#include "getopts.h"
#include "ctf.h"
#include <stddef.h>

#define CORRECT_PHASE					( 1<<0 )
#define CORRECT_WIENER					( 1<<1 )
#define CORRECT_BACKGROUND				( 1<<2 )
#define CORRECT_ENVELOPE				( 1<<3 )
#define CORRECT_APPLY					( 1<<4 )

typedef struct CTFParamsSt {
	
	char img_path[1024];
	char out_path[1024];
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
	
	sprintf(c->img_path,"./");
	sprintf(c->out_path,"./");
	
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
		count += sscanf(line," Final Defocus (m,m,deg): %le %le %le",&(c->defocus_x),&(c->defocus_y),&(c->astig_angle));
		count += sscanf(line," Amplitude Contrast: %le",&(c->amp_c));
		count += sscanf(line," Voltage: %le",&(c->kv));
		count += sscanf(line," Voltage (kV): %le",&(c->kv));
	 	count += sscanf(line," Spherical Aberration: %le",&(c->cs));
	 	count += sscanf(line," Spherical Aberration (mm): %le",&(c->cs));
		count += sscanf(line," Angstroms per pixel: %le",&(c->apix));
		
	}
	
	if (fabs(c->defocus_x) > fabs(c->defocus_y) ) {
		fprintf(stderr, "Using old values of ace2\nWARNING astig angle could be off by 90 degreees\n\n");
		c->defocus_x = -1.0 * c->defocus_x;
		c->defocus_y = -1.0 * c->defocus_y;
		c->cs = c->cs * 1e3;
		c->astig_angle = c->astig_angle*DEG;
	}


	fclose(fp);
	
	sprintf(c->out_path,"%s.corrected.mrc",c->img_path);
	
	return count;
	
}

CTFParams parseACE2CorrectOptions( int argc, char **argv ) {
	
	CTFParams ctfp = newCTFParams();
	
	if ( ctfp == NULL ) {
		fprintf(stderr,"ERROR: Could not allocate needed memory during option parsing\n");
		exit(-1);
	}
	
	struct options opts[] = {
		{ 1,	NULL,	"Path to CTF estimate file",	 			"ctf",			1 },
		{ 2,	NULL,	"Path to image file",	 					"img",			1 },
		{ 3,	NULL,	"Microscope voltage in kilovolts",			"kv",			1 },
		{ 4,	NULL,	"Microscope Spherical Aberration in mm",	"cs",			1 },
		{ 5,	NULL,	"Angstroms per pixel",						"apix",			1 },
		{ 6,	NULL,	"Defocus: x,y,angle in m,m,degrees (underfocus is +)",		"df",			1 },
		{ 7,	NULL,	"Correct only phase signs",	  				"phase",		0 },
		{ 8,	NULL,	"Correct using wiener filter",				"wiener",		1 },
		{ 9,	NULL,	"Apply the given CTF",						"apply", 		0 },
		{ 10,	NULL,	"Set output path",							"out",			1 },
		{ 11,   NULL,	"Override amplitude contrast",				"ampc",			1 },
		{ 0,	NULL,	NULL,										NULL,			0 }
	};
	
	int option = 0;
	char arg[1024];
		
	while ( ( option = getopts(argc,argv,opts,arg) ) != 0 ) {
		fprintf(stderr,"Parsing option: %d %s\n",option,arg);
		switch ( option ) {
			case -1:
				fprintf(stderr,"No memory for parsing, exiting!!!\n");
				exit(-1);
			case  1:
				if ( parseACE2CTFFile(arg,ctfp) != 8 ) fprintf(stderr,"!!!! Incomplete ACE2 CTF File !!!!\n");
				break;
			case 2:
				strcpy(ctfp->img_path,arg);				
				sprintf(ctfp->out_path,"%s.corrected.mrc",ctfp->img_path);
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
				ctfp->astig_angle = ctfp->astig_angle;
				break;
			case 7:
				ctfp->correction_type &= !CORRECT_WIENER;
				ctfp->correction_type &= !CORRECT_APPLY;
				ctfp->correction_type |=  CORRECT_PHASE;
				break;
			case 8:
				ctfp->correction_type &= !CORRECT_PHASE;
				ctfp->correction_type &= !CORRECT_APPLY;
				ctfp->correction_type |=  CORRECT_WIENER;
				sscanf(arg,"%le",&(ctfp->wiener));
				break;
			case 9: 
				ctfp->correction_type &= !CORRECT_PHASE;
				ctfp->correction_type &= !CORRECT_WIENER;
				ctfp->correction_type |=  CORRECT_APPLY;
				break;
			case 10:
				strcpy(ctfp->out_path,arg);
				break;
			case 11:
				sscanf(arg,"%le",&(ctfp->amp_c));
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
	fprintf(fp,"Angstoms per Pixel: %le\n",p->apix);
	fprintf(fp,"High Tension (kV): %f\n",p->kv);
	fprintf(fp,"Spherical Abberation, CS (mm): %f\n",p->cs);
	fprintf(fp,"Defocus(1): %le, Defocus(2): %le\n",p->defocus_x,p->defocus_y);
	fprintf(fp,"  in meters with underfocus positive |Def1| < |Def2|\n");
	fprintf(fp,"Astigmatism Angle (Degrees): %f\n",p->astig_angle);
	fprintf(fp,"  major axis along x-axis is zero, counter-clockwise is +\n");
	fprintf(fp,"Amplitude Contrast: %f\n",p->amp_c);
	
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
	f64 df2 = ctfp->defocus_x;
	f64 df1 = ctfp->defocus_y;
	f64 dfr = ctfp->astig_angle/DEG - 1.570796327;
	f64 ac 	= ctfp->amp_c;
	f64 apix = ctfp->apix;
	f64 cs = ctfp->cs*1e-3;
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

	fprintf(stderr,"g2DCTF(%.1e,%.1e,%.1e,%d,%d,%.1e,%.1e,%.1e,%.1f)\n",
		df2,df1,dfr,rows,cols,apix,cs,kv,ac);

	ArrayP ctf = g2DCTF(df1,df2,dfr,rows,cols,apix,cs,kv,ac);
	
	fprintf(stderr,"\t\t\tDONE in %2.2f secs\n",CPUTIME-t1);
	
//---------Correct CTF of image----------------------------------------------------------------	
	
	f64 * cp = [ctf data];
	c64 * ip = [image data];
	u32 i, size = [image numberOfElements];
		
	t1 = CPUTIME;
	
	if ( cty & CORRECT_PHASE ) {
		fprintf(stderr,"Correcting image using phase flips...  ");
		#pragma omp for
		for(i=0;i<size;i++) {
			if ( cp[i] < 0.0 ) {
				ip[i] = -ip[i];
			}
		}
	}
	if ( cty & CORRECT_WIENER ) {
		fprintf(stderr,"Correcting image using wiener filter...");
		#pragma omp for
		for(i=0;i<size;i++) {
			ip[i] = (ip[i]*cp[i])/(cp[i]*cp[i]+snr);
		}
	}
	if ( cty & CORRECT_APPLY ) {
		fprintf(stderr,"Applying the CTF for Dmitry...         ");
		#pragma omp for
		for(i=0;i<size;i++) {
			ip[i] = ip[i]*cp[i];
		}
	}
	
	fprintf(stderr,"\tDONE in %2.2f secs\n",CPUTIME-t1);
	
//---------Perform inverse FFT using FFTW c2r transform-----------------------------------------		
	
	t1 = CPUTIME;	
	fprintf(stderr,"Performing inverse fft...");
	
	[image c2rfftc];
	
	fprintf(stderr,"\t\tDONE in %2.2f secs\n",CPUTIME-t1);
	
//---------Writing corrected image--------------------------------------------------------------		
	
	fprintf(stderr,"Saving corrected image to: %s\n",ctfp->out_path);
	
	[image writeMRCFile:ctfp->out_path];
	
	[image release];
	[ctf release];

	fprintf(stderr,"\nTotal Correction Time: %2.2f secs\n",CPUTIME-t0);
		
}
