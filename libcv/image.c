#include "defs.h"
#include "ellipsefit.h"

Image ReadPGM(FILE *fp);
Image ReadPPM(FILE *fp);
void SkipComments(FILE *fp);

Image CreateImage(int rows, int cols ) {
    Image im = (Image)malloc(sizeof(struct ImageSt));
    im->rows = rows;
    im->cols = cols;
	im->pixels = AllocIMatrix(rows,cols,0,0);
    im->next = NULL;
	im->maxv = -1;
	im->minv =  1;
    return im;
}

void SetImagePixel1( Image im, int row, int col, int val ) {
	if ( row<0||col<0||row>=im->rows||col>=im->cols ) return;
	im->pixels[row][col] = val;
}

void SetImagePixel3( Image im, int row, int col, int r, int g, int b ) {
	if ( row<0||col<0||row>=im->rows||col>=im->cols ) return;
	im->pixels[row][col] = PIX3(r,g,b);
}

Image ReadPGMFile(char *filename) {
    FILE *file;
    file = fopen (filename, "rb");
    if (! file)
	FatalError("Could not open file: %s", filename);
    return ReadPGM(file);
}

Image ReadPGM(FILE *fp) {

  int char1, char2, rows, cols, max, c1, c2, c3, r, c;
  
  Image nextimage;
  
  char1 = fgetc(fp);
  char2 = fgetc(fp);
  SkipComments(fp);
  c1 = fscanf(fp, "%d", &cols);
  SkipComments(fp);
  c2 = fscanf(fp, "%d", &rows);
  SkipComments(fp);
  c3 = fscanf(fp, "%d", &max);
  
  if (char1 != 'P' || char2 != '5' || c1 != 1 || c2 != 1 || c3 != 1 || max > 255) return NULL;

  fgetc(fp); 

  Image image = CreateImage(rows, cols);
  for (r=0;r<rows;r++) for (c=0;c<cols;c++) SetImagePixel1(image,r,c,fgetc(fp));

  SkipComments(fp);
  if (getc(fp) == 'P') {
    ungetc('P', fp);
    nextimage = ReadPGM(fp);
    image->next = nextimage;
  }
  
  fclose(fp);
  
  image->maxv = 255;
  image->minv = 0;
  
  return image;
  
}

void WritePGM(char *name, Image image) {

    int r, c, val;
    FILE *fp = fopen(name, "w");
    fprintf(fp, "P5\n%d %d\n255\n", image->cols, image->rows);

    for (r = 0; r < image->rows; r++) for (c = 0; c < image->cols; c++) {
		val = image->pixels[r][c];
		fputc(MAX(0, MIN(255, val)), fp);
	}
      
	fclose(fp);
	
}

void ClearImage( Image out, int val ) {
	int k, max = out->rows*out->cols, *pix = out->pixels[0];
	for (k=0;k<max;k++) pix[k] = val;

}

void FreeImage( Image out ) {
	if ( out != NULL ) {
		if ( out->pixels != NULL ) 	{
			if ( out->pixels[0] != NULL ) {
				free(out->pixels[0]);
			}
			free(out->pixels);
		}
		free(out);
	}
}

Image ReadPPMFile( char *filename ) {
	FILE *file;
	file = fopen (filename, "rb");
	if ( !file ) return NULL;
	return ReadPPM(file);
}

Image ReadPPM( FILE *fp ) {

  	int char1, char2, width, height, max, c1, c2, c3, r, c;
	
	Image nextimage;
	
  	char1 = fgetc(fp);
  	char2 = fgetc(fp);
  	SkipComments(fp);
  	c1 = fscanf(fp, "%d", &width);
  	SkipComments(fp);
  	c2 = fscanf(fp, "%d", &height);
  	SkipComments(fp);
  	c3 = fscanf(fp, "%d", &max);

	if (char1 != 'P' || char2 != '6' || c1 != 1 || c2 != 1 || c3 != 1 || max > 255) return NULL;

	fgetc(fp); 

	Image image = CreateImage(height, width);
	for (r = 0; r < height; r++) for (c = 0; c < width; c++) SetImagePixel3(image,r,c,fgetc(fp),fgetc(fp),fgetc(fp));
	
	SkipComments(fp);
  	
	if (getc(fp) == 'P') {
		ungetc('P', fp);
		nextimage = ReadPPM(fp);
		image->next = nextimage;
	}
  	
	fclose(fp);
	
	image->maxv = 255;
	image->minv = 0;
  
	return image;
  
}

void SkipComments(FILE *fp) {
    int ch;
    fscanf(fp," ");      
	while ((ch = fgetc(fp)) == '#') {
		while ((ch = fgetc(fp)) != '\n'  &&  ch != EOF);
		fscanf(fp," ");
    }
    ungetc(ch, fp);
}


void WritePPM( char *name, Image image) {

    int r, c;
    FILE *fp = fopen(name, "w");
    fprintf(fp, "P6\n%d %d\n255\n", image->cols, image->rows);

    for (r = 0; r < image->rows; r++) {
      for (c = 0; c < image->cols; c++) {
	  	int val = image->pixels[r][c];
		fputc( MAX(0,MIN(255,PIXR(val))), fp);
		fputc( MAX(0,MIN(255,PIXG(val))), fp);
		fputc( MAX(0,MIN(255,PIXB(val))), fp);
      }
	}
      
    fclose(fp);
}

Image CopyImage( Image or ) {
	int maxrow = or->rows;
	int maxcol = or->cols;
	Image co = CreateImage(maxrow,maxcol);
	memcpy(co->pixels[0],or->pixels[0],sizeof(int)*maxrow*maxcol);
	return co;
}

Image ConvertImage1( Image im ) {
	if ( im == NULL ) return im;
	int k, *pix = im->pixels[0];
	for (k=0;k<im->rows*im->cols;k++) pix[k] = pix[k] + (pix[k]<<8) + (pix[k]<<16);
	return im;
}

Image ConvertImage3( Image im ) {
	if ( im == NULL ) return im;
	int k, *pix = im->pixels[0];
	for (k=0;k<im->rows*im->cols;k++) pix[k] = 0.33*(pix[k]%256) + 0.33*((pix[k]>>8)%256) + 0.33*((pix[k]>>16)) + 0.5;
	return im;
}

char ImageGood( Image image ) {
	if ( image == NULL ) return FALSE;
	if ( image->pixels == NULL ) return FALSE;
	if ( image->pixels[0] == NULL ) return FALSE;
	return TRUE;
}

void DrawPointStack( PointStack points, Image out, int v ) {
	
	if ( !PointStackGood(points) || !ImageGood(out) ) return;
	
	while ( PointStackCycle(points) ) {
		Point p = CyclePointStack(points);
		SetImagePixel1(out,p->row,p->col,v);
	}
	
}

void DrawEllipse( Ellipse ellipse, Image out, int v ) {

	if ( ellipse == NULL || !ImageGood(out) ) return;	
	int maxrow = out->rows-1;
	int maxcol = out->cols-1;
	int **pix = out->pixels;
	double A1 = ellipse->A;
	double B1 = ellipse->B;
	double C1 = ellipse->C;
	double D1 = ellipse->D;
	double E1 = ellipse->E;
	double F1 = ellipse->F;
	double maj = ellipse->majaxis;
	double min = ellipse->minaxis;
	double ero = ellipse->erow;
	double eco = ellipse->ecol;
	double phi = ellipse->phi;
		
	Ellipse e2 = NewEllipse(ero,eco,maj+2,min+2,phi);
	
	double A2 = e2->A;
	double B2 = e2->B;
	double C2 = e2->C;
	double D2 = e2->D;
	double E2 = e2->E;
	double F2 = e2->F;
	
	int minr = e2->minr;
	int maxr = e2->maxr;
	int minc = e2->minc;
	int maxc = e2->maxc;
	
	free(e2);
	
	minr = BOUND(0,minr,maxrow);
	maxr = BOUND(0,maxr,maxrow);
	minc = BOUND(0,minc,maxcol);
	maxc = BOUND(0,maxc,maxcol);
	
	int row, col;
	for(row=minr;row<=maxr;row++) {
		for(col=minc;col<=maxc;col++) {
			double r = row + 0.5;
			double c = col + 0.5;
			double vx = A1*r*r + B1*r*c + C1*c*c + D1*r + E1*c + F1;
			double vy = A2*r*r + B2*r*c + C2*c*c + D2*r + E2*c + F2;
			if ( vy <= 0.0 && vx >= 0.0 ) pix[row][col] = v;
	}}
	
}
	
void FastLineDraw(int y0, int x0, int y1, int x1, Image out, int v ) {
	
	int maxcol = out->cols, maxrow = out->rows, *pix = out->pixels[0];
	
	int dy = y1 - y0;
	int dx = x1 - x0;
	int stepx, stepy;
	
	if (dy < 0) { dy = -dy;  stepy = -maxcol; } else { stepy = maxcol; }
	if (dx < 0) { dx = -dx;  stepx = -1; } else { stepx = 1; }
	dy <<= 1;
	dx <<= 1;

	y0 *= maxcol;
	y1 *= maxcol;
	pix[x0+y0] = v;
	if (dx > dy) {
		int fraction = dy - (dx >> 1);
		while (x0 != x1) {
			if (fraction >= 0) {
				y0 += stepy;
				fraction -= dx;
			}
			x0 += stepx;
			fraction += dy;
			if ( x0 < 0 || x0 >= maxcol || y0 < 0 || y0 >= maxrow*maxcol ) continue;
			pix[x0+y0] = v;
		}
	} else {
		int fraction = dx - (dy >> 1);
		while (y0 != y1) {
			if (fraction >= 0) {
				x0 += stepx;
				fraction -= dy;
			}
			y0 += stepy;
			fraction += dx;
			if ( x0 < 0 || x0 >= maxcol || y0 < 0 || y0 >= maxrow*maxcol ) continue;
			pix[x0+y0] = v;
		}
	}
}
	
Image CombineImagesVertically(Image im1, Image im2) {

    int rows, cols, r, c;

    rows = im1->rows + im2->rows;
    cols = MAX(im1->cols, im2->cols);
    Image result = CreateImage(rows, cols);

    for (r = 0; r < rows; r++) for (c = 0; c < cols; c++) result->pixels[r][c] = 0;
    for (r = 0; r < im1->rows; r++) for (c = 0; c < im1->cols; c++) result->pixels[r][c] = im1->pixels[r][c];
    for (r = 0; r < im2->rows; r++) for (c = 0; c < im2->cols; c++) result->pixels[r + im1->rows][c] = im2->pixels[r][c];
	
	result->maxv = MAX(im1->maxv,im2->maxv);
	result->minv = MIN(im1->minv,im2->minv);
	
    return result;
	
}

Image CombineImagesHorizontally(Image im1, Image im2) {

    int rows, cols, r, c;

    rows = MAX(im1->rows, im2->rows);
    cols = im1->cols + im2->cols;
    Image result = CreateImage(rows, cols);

    for (r = 0; r < rows; r++) for (c = 0; c < cols; c++) result->pixels[r][c] = 0;
    for (r = 0; r < im1->rows; r++) for (c = 0; c < im1->cols; c++) result->pixels[r][c] = im1->pixels[r][c];
    for (r = 0; r < im2->rows; r++) for (c = 0; c < im2->cols; c++) result->pixels[r][c+im1->cols] = im2->pixels[r][c];
  	
	result->maxv = MAX(im1->maxv,im2->maxv);
	result->minv = MIN(im1->minv,im2->minv);
	
    return result;
	
}

void GaussianBlurImage( Image im, float sigma ) {
	
	int row, col, i;
	int maxr = im->rows-1, maxc = im->cols-1;
	
	int kernelsize = sigma*3*2;
	if (kernelsize%2 == 0) kernelsize++;
	int krad=kernelsize/2;
	
	int **p1 = im->pixels;
	int **p2 = AllocIMatrix(im->rows,im->cols,0,0);
	float *kernel = CreateGaussianKernel( kernelsize, sigma );

	for (row=0;row<=maxr;++row) {
		for (col=0;col<=maxc;++col) {
			float sum = 0;
			for (i=-krad;i<=krad;++i) {
				int absPos=col+i;
				if (absPos<0) absPos=0;
				else if (absPos>maxc) absPos=maxc;
				sum += kernel[i]*p1[row][absPos];
			}
			p2[col][row] = sum+0.5;
	}}
	
	for (row=0;row<=maxc;++row) {
		for (col=0;col<=maxc;++col) {
			float sum = 0; 
			for (i=-krad;i<=krad;++i) {
				int absPos=col+i;
				if (absPos<0) absPos=0;
				else if (absPos>maxc) absPos=maxc;
				sum += kernel[i]*p2[row][absPos];
			}
			p1[col][row] = sum+0.5;
			
		}
	}
	
	free(kernel-krad);
	FreeIMatrix(p2,0,0);

}

void SplineImage( Image im, float **v2 ) {
	int j;
	for (j=0;j<im->rows;j++) ISpline(im->pixels[j],im->cols,v2[j]);
}

int SplintImage( Image im, float **v2, float row, float col ) {
	int j;
	float *ytmp, *yytmp, val;
	ytmp  = malloc(sizeof(float)*im->cols);
	yytmp = malloc(sizeof(float)*im->cols);
	for (j=0;j<im->rows;j++) ISplint(im->pixels[j],v2[j],im->cols,col,&yytmp[j]);
	FSpline(yytmp,im->rows,ytmp);
	FSplint(yytmp,ytmp,im->rows,row,&val);
	free(ytmp); free(yytmp);
	return val+0.5;
}

void WrapGaussianBlur1D( float *line, int l, int r, float sigma ) {
	
	int i, k;
	int kernelsize = sigma*3*2+1;
	int radius = sigma*3;
	float *kernel = CreateGaussianKernel(kernelsize,sigma);
	int buffersize = r-l+1;
	float *buffer = malloc(sizeof(float)*buffersize)-l;
	int loff = r + 1;
	int roff = l - 1 - r;
	for (i=l;i<=r;i++) buffer[i] = line[i];
	for (i=l;i<=r;i++) {
		line[i] = 0;
		for (k=-radius;k<=radius;k++) {
			int pos = i+k;
			if ( pos < l ) pos += loff;
			if ( pos > r ) pos += roff;
			line[i] += buffer[pos]*kernel[k];
		}
	}
	free(buffer+l); free(kernel-radius);
	
}

int InterpolatePixelValue( Image im, float row, float col ) {
	int maxrow = im->rows-1;
	int maxcol = im->cols-1;
	int irow = row;
	int icol = col;
	if ( row < 0 || col < 0 || row >= maxrow || col >= maxcol ) return -1;
	int *p1 = &(im->pixels[irow][icol]);
	int a = *p1;
	int b = *(p1+=1);
	int c = *(p1+=maxcol);
	int d = *(p1+=1);
	float rwgt2 = row - irow;
	float rwgt1 = 1 - rwgt2;
	float cwgt2 = col - icol;
	float cwgt1 = 1 - cwgt2;
	return a*rwgt1*cwgt1+b*rwgt1*cwgt2+c*rwgt2*cwgt1+d*rwgt2*cwgt2+0.5;
}

void AffineTransformImage( Image from, Image to, double **tr, double **it ) {

	int row, col;
	int **p1 = to->pixels;	
	
	float crshift = it[1][0];
	float ccshift = it[1][1];
	float rrshift = it[0][0];
	float rcshift = it[0][1];
	
	float rad1 = 0.5;
	
	float r1 =  it[0][0]*rad1;
	float c1 =  it[0][1]*rad1;  
	float r2 =  it[1][0]*rad1;
	float c2 =  it[1][1]*rad1;
	
	float r3 =  it[0][0]*rad1+it[1][0]*rad1;
	float c3 =  it[0][1]*rad1+it[1][1]*rad1;
	float r4 =  it[0][0]*rad1-it[1][0]*rad1;
	float c4 =  it[0][1]*rad1-it[1][1]*rad1;
	float r5 = -it[0][0]*rad1-it[1][0]*rad1;
	float c5 = -it[0][1]*rad1-it[1][1]*rad1;
	float r6 = -it[0][0]*rad1+it[1][0]*rad1;
	float c6 = -it[0][1]*rad1+it[1][1]*rad1;
	
	float nrow = it[2][0];
	float ncol = it[2][1];

	for (row=0;row<to->rows;row++) {
		float tnrow = nrow;
		float tncol = ncol;
		for (col=0;col<to->cols;col++) {
			int q1 = InterpolatePixelValue(from,tnrow,tncol);
			int q2 = InterpolatePixelValue(from,tnrow+r1,tncol+c1);
			int q3 = InterpolatePixelValue(from,tnrow-r1,tncol-c1);
			int q4 = InterpolatePixelValue(from,tnrow+r2,tncol+c2);
			int q5 = InterpolatePixelValue(from,tnrow-r2,tncol-c2);
			int q6 = InterpolatePixelValue(from,tnrow+r3,tncol+c3);	
			int q7 = InterpolatePixelValue(from,tnrow+r4,tncol+c4);	
			int q8 = InterpolatePixelValue(from,tnrow+r5,tncol+c5);	
			int q9 = InterpolatePixelValue(from,tnrow+r6,tncol+c6);
			if (q2<0||q3<0||q4<0||q5<0||q6<0||q7<0||q8<0||q9<0) p1[row][col] = -1; 
			else p1[row][col] = ( q1 + ((q2+q3+q4+q5)>>1) + ((q6+q7+q8+q9)>>2) ) >> 2;
			tnrow+=crshift;
			tncol+=ccshift;
		}
		nrow+=rrshift;
		ncol+=rcshift;
	}
		
}

void FindImageLimits( Image im ) {
	
	int *p = im->pixels[0];
	int k, size = im->rows*im->cols;
	
	int maxv = *p;
	int minv = *p;
	
	for (k=0;k<size;k++,p++) {
		maxv = MAX(*p,maxv);
		minv = MIN(*p,minv);
	}
	
	im->maxv = maxv;
	im->minv = minv;
	
}

int ImageRangeDefined( Image im ) {
	if ( im->maxv < im->minv ) return FALSE;
	return TRUE;
}

FVec GenerateImageHistogram( Image im ) {
	int *p = im->pixels[0];
	int k, size = im->rows*im->cols;
	if ( !ImageRangeDefined(im) ) FindImageLimits(im);
	FVec histogram = NewFVec(im->minv,im->maxv);
	for (k=0;k<size;k++,p++) histogram->values[*p]++;
	return histogram;
}

Image EnhanceImage( Image im, int min, int max, float minh, float maxh ) {

	if ( !ImageGood(im) || minh >= 1 || maxh >= 1 || min > max ) return im;
	
	int totalsize = im->rows*im->cols;
	
	minh = totalsize*minh;
	maxh = totalsize*maxh;
	
	FVec hist = GenerateImageHistogram( im );

	int minv = im->minv, maxv = im->maxv, sum;
	for ( sum = 0; sum + hist->values[minv] < minh; sum += hist->values[minv++] );
	for ( sum = 0; sum + hist->values[maxv] < maxh; sum += hist->values[maxv--] );
	
	FreeFVec(hist);
	
	float normalizingfactor = (float)max/(maxv-minv+min);
	int *p = im->pixels[0], k;
	for (k=0;k<totalsize;k++,p++) *p = MAX(0,MIN(max,(*p-minv+min)*normalizingfactor+0.5));
	
	im->maxv = max;
	im->minv = min;
	
	return im;
	
}

void PascalBlurImage( Image im, float sigma ) {
	
	int maxrow = im->rows;
	int maxcol = im->cols;
	
	int tmp1, tmp2, SR0, SR1, row, col, i;
	int iterations = sigma*sigma*4+0.5;
	int SC0[maxcol];
	int SC1[maxcol];

	for (i=1;i<=iterations;++i) {
		for (i=0;i<maxcol;i++) SC0[i] = 0;
		for (i=0;i<maxcol;i++) SC1[i] = 0;
		for (row=1;row<maxrow;++row) {
			SR0 = SR1 = 0;
			for ( col=1;col<maxcol;++col) {
				tmp1 = im->pixels[row][col];
				tmp2 = SR0 + tmp1;
				SR0 = tmp1;
				tmp1 = SR1 + tmp2;
				SR1 = tmp2;
				tmp2 = SC0[col] + tmp1;
				SC0[col] = tmp1;
				im->pixels[row-1][col-1] = (SC1[col]+tmp2+8)>>4;
				SC1[col] = tmp2;
			}
		}
	}
}

void DrawFVec(FVec sizes, int im_rmin, int im_cmin, int im_rmax, int im_cmax, int v, Image out ) {
	
	int maxcol = out->cols-1;
	int maxrow = out->rows-1;
	
	
	int k, l = sizes->l, r = sizes->r;
	float large = sizes->values[l], small = sizes->values[l];
	for (k=l;k<=r;k++) large = MAX(large,sizes->values[k]);
	for (k=l;k<=r;k++) small = MIN(small,sizes->values[k]);
	
	int vec_cmax = r;
	int vec_cmin = l;
	int vec_rmax = large;
	int vec_rmin = small;

	double **tr = AllocDMatrix(3,3,0,0);
	CreateDirectAffineTransform( vec_rmax,vec_cmax, vec_rmin,vec_cmin, vec_rmin,vec_cmax, im_rmin,im_cmax, im_rmax,im_cmin, im_rmax,im_cmax, tr,NULL);

	for (k=l;k<r;k++) {
	
		float r1 = sizes->values[k];
		float r2 = sizes->values[k+1];
		float c1 = k;
		float c2 = k+1;
		
		float r1n = r1*tr[0][0]+c1*tr[1][0]+tr[2][0];
		float c1n = r1*tr[0][1]+c1*tr[1][1]+tr[2][1];
		float r2n = r2*tr[0][0]+c2*tr[1][0]+tr[2][0];
		float c2n = r2*tr[0][1]+c2*tr[1][1]+tr[2][1];

		r1n = MAX(0,MIN(r1n,maxrow));
		c1n = MAX(0,MIN(c1n,maxcol));
		r2n = MAX(0,MIN(r2n,maxrow));
		c2n = MAX(0,MIN(c2n,maxcol));
		
		FastLineDraw(r1n,c1n,r2n,c2n,out,v);
		
	}

	FreeDMatrix(tr,0,0);
	
}
