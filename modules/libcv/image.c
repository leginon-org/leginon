#include "image.h"

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
	if ( out == NULL ) return;
	FreeIMatrix(out->pixels,0,0);
	free(out);
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
	for (r = 0; r < height; r++) {
		for (c = 0; c < width; c++) {
			int rv = fgetc(fp);
			int gv = fgetc(fp);
			int bv = fgetc(fp);
			SetImagePixel1(image,r,c,PIX3(rv,gv,bv));
	}}
	
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
    ch = fscanf(fp," ");      
	while ((ch = fgetc(fp)) == '#') {
		while ((ch = fgetc(fp)) != '\n'  &&  ch != EOF);
		ch = fscanf(fp," ");
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

char ImageIsGood( Image image ) {
	if ( image == NULL ) return FALSE;
	if ( image->pixels == NULL ) return FALSE;
	if ( image->pixels[0] == NULL ) return FALSE;
	return TRUE;
}

void DrawPolygon( Polygon poly, Image out, int v ) {
	
	if ( !PolygonIsGood(poly) || !ImageIsGood(out) ) return;
	
	int i, size = poly->numberOfVertices;
	Point p = poly->vertices;
	for(i=0;i<size;i++) {
		int k = ( i + 1 ) % size;
		float x1 = p[i].x, y1 = p[i].y;
		float x2 = p[k].x, y2 = p[k].y;
		FastLineDraw(x1,y1,x2,y2,out,v);
	}
	
}

void DrawEllipse( Ellipse ellipse, Image out, int v ) {

	if ( ellipse == NULL || !ImageIsGood(out) ) return;	
	int maxrow = out->rows-1;
	int maxcol = out->cols-1;
	int **pix = out->pixels;
	double A1 = ellipse->A;
	double B1 = ellipse->B;
	double C1 = ellipse->C;
	double D1 = ellipse->D;
	double E1 = ellipse->E;
	double F1 = ellipse->F;
	double maj = ellipse->majorAxis;
	double min = ellipse->minorAxis;
	double ero = ellipse->x;
	double eco = ellipse->y;
	double phi = ellipse->phi;
		
	Ellipse e2 = NewEllipse(ero,eco,maj+2,min+2,phi);
	
	double A2 = e2->A;
	double B2 = e2->B;
	double C2 = e2->C;
	double D2 = e2->D;
	double E2 = e2->E;
	double F2 = e2->F;
	
	int minr = e2->topBound;
	int maxr = e2->bottomBound;
	int minc = e2->leftBound;
	int maxc = e2->rightBound;
	
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

Image GaussianBlurImage( Image im, float sigma ) {
	
	if ( sigma <= 0 ) return im;
	
	int row, col, i;
	int maxr = im->rows-1, maxc = im->cols-1;
	
	int kernelsize = sigma*3*2;
	kernelsize = MAX(3,kernelsize);
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
				absPos = BOUND(0,absPos,maxc);
				int pix = p1[row][absPos];
				if ( pix < 0 ) continue;
				sum += kernel[i]*pix;
			}
			p2[row][col] = sum + 0.5;
	}}
	
	for (col=0;col<=maxc;++col) {
		for (row=0;row<=maxr;++row) {
			float sum = 0; 
			for (i=-krad;i<=krad;++i) {
				int absPos=row+i;
				absPos = BOUND(0,absPos,maxr);
				int pix = p2[absPos][col];
				if ( pix < 0 ) continue;
				sum += kernel[i]*pix;
			}
			p1[row][col] = sum + 0.5;
			
		}
	}
	
	free(kernel-krad);
	FreeIMatrix(p2,0,0);
	
	return im;
	
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

void GaussianBlur1D( float *line, int l, int r, float sigma ) {
	
	int i, k;
	int kernelSize = sigma*3*2+1;
	kernelSize = MAX(3,kernelSize);
	int radius = kernelSize/2;
	float *kernel = CreateGaussianKernel(kernelSize,sigma);
	int buffersize = r-l+1;
	float *buffer = malloc(sizeof(float)*buffersize);
	buffer = buffer - l;
	for (i=l;i<=r;i++) buffer[i] = line[i];
	for (i=l;i<=r;i++) {
		line[i] = 0;
		for (k=-radius;k<=radius;k++) {
			int pos = i+k;
			if ( pos < l ) continue;
			if ( pos > r ) continue;
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

	float nrow = it[2][0];
	float ncol = it[2][1];

	for (row=0;row<to->rows;row++) {
		float tnrow = nrow;
		float tncol = ncol;
		for (col=0;col<to->cols;col++) {
			int q1 = InterpolatePixelValue(from,tnrow,tncol); // Uses bi-linear interpolation
			if ( q1 < 0 ) to->pixels[row][col] = -10000;
			else to->pixels[row][col] = q1;
			tnrow+=it[1][0];
			tncol+=it[1][1];
		}
		nrow+=it[0][0];
		ncol+=it[0][1];
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
	FVec histogram = FVecNew(im->minv,im->maxv);
	for (k=0;k<size;k++,p++) {
		histogram->values[*p]++;
	}
	return histogram;
}

Image EnhanceImage( Image im, int min, int max, float minh, float maxh ) {

	if ( !ImageIsGood(im) || minh >= 1 || maxh >= 1 || min > max ) return im;
	
	int totalsize = im->rows*im->cols;
	
	minh = totalsize * minh;
	maxh = totalsize * maxh;

	FVec hist = GenerateImageHistogram( im );
	float *LUT = hist->values;
	
	int minv = im->minv, maxv = im->maxv, sum;
	for ( sum = 0; sum + LUT[minv] < minh; sum += LUT[minv++] );
	for ( sum = 0; sum + LUT[maxv] < maxh; sum += LUT[maxv--] );
	
	int i;
	float norm =  (float)(max-min) / (maxv-minv);
	
	for (i=minv+1;i<maxv;i++) LUT[i] = (i-minv)*norm + 0.5;
	for (i=im->minv;i<=minv;i++) LUT[i] = min;
	for (i=maxv;i<=im->maxv;i++) LUT[i] = max;
	
	int *p = im->pixels[0], k;
	for (k=0;k<totalsize;k++,p++) *p = LUT[*p];

	im->maxv = max;
	im->minv = min;
	
	FVecFree(hist);
	
	return im;
	
}

Image PascalBlurImage( Image im, float sigma ) {
	
	int maxrow = im->rows;
	int maxcol = im->cols;
	
	int tmp1, tmp2, SR0, SR1, row, col, i;
	int iterations = sigma*sigma*4;
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
	
	return im;
	
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

void SeparableAffineTransform( Image im1, Image im2, double **TR, double **IT ) {
	
	int sourceRows = im1->rows;
	int sourceCols = im1->cols;
	int destinationRows = im2->rows;
	int destinationCols = im2->cols;
	
	static int **b1 = NULL;
	static int oldb1rows = 0;
	static int oldb1cols = 0;
	
	if ( oldb1rows != sourceRows || oldb1cols != destinationCols ) {
		FreeIMatrix(b1,0,0);
		b1 = AllocIMatrix(sourceRows,destinationCols,0,0);
		oldb1rows = sourceRows;
		oldb1cols = destinationCols;
	}
	
	int **p1 = im1->pixels;
	int **p2 = im2->pixels;

	int r,c;
	
	/*	
		If the forward transform from source to patch is :		[a d 0]
																[b e 0]
																[c f 1]
		
		and the inverse transform from patch to source is :		[g j 0]
																[h k 0]
																[i l 1]
		
		Then the col only, first stage forward transform is:	[1 d 0]
																[0 e 0]
																[0 f 1]
		
		and the col only first stage inverse transform is:		[1    j/g    0]
																[0 k-(h*j)/g 0]
																[0 l-(i*j)/g 1]
																
		The row only, second stage forward transform is:		[a-(d*b)/e 0 0]
																[   b/e    0 0]
																[c-(f*b)/e 0 1]
																
		The row only, second stage inverse transform is:		[g 0 0]
																[h 1 0]
																[i 0 1]
		
	*/
	
	
	float TR1 = TR[0][0]-(TR[0][1]*TR[1][0])/TR[1][1];
	float TR5 = TR[1][1];
	
	float IT1 = IT[0][0];
	float IT2 = IT[1][0];
	float IT3 = IT[2][0];
	float IT4 = IT[0][1]/IT[0][0];
	float IT5 = IT[1][1]-(IT[1][0]*IT[0][1])/IT[0][0];
	float IT6 = IT[2][1]-(IT[2][0]*IT[0][1])/IT[0][0];
	
	
	/* We kknow ahead of time all the rows in the source image might not go into the 
		patch image.  Here we find the row values of the four corners of the patch 
		transformed into the source image.  Everything in the patch image will come 
		from between the largest and smallest of these numbers so we can clip them to
		the image bounds and use them to constrain the number of rows that go through
		the one-dimensional scale and skew operation. */
	  
	float r1 = IT[2][0];
	float r2 = destinationRows*IT[0][0] + r1;
	float r3 = destinationCols*IT[1][0] + r1;
	float r4 = destinationRows*IT[0][0] + r3;
	
	int minRow = MAX(0,MIN(r1,MIN(r2,MIN(r3,r4))));
	int maxRow = MIN(sourceRows,MAX(r1,MAX(r2,MAX(r3,r4)))+1);
	
	/* If the maximum and minimum are outside the source image then there will be
		no image in the patch!! Return if this is the case */
		
	if ( minRow >= sourceRows ) return;
	if ( maxRow < 0 ) return;
	
	float sS, oS, iS;
	
	
	/* While this code may look tricky what it is doing is moving through the
		rows in the patch image and filling in values from the source.  This
		is done continuously, and the rate between outputing pixels into the patch
		and reading them from the source is controlled by value oS which is equal to
		IT5.  This value basically describes how many input pixels must go into each output.
		The start position for the patch is always set to 0, since we want to completely
		fill in the patch image, while the beginning position in the source is set by the
		value sS.  This value is set once at the beginning and merely incremented by its
		derivative IT4 or IT2, depending on wether we are transforming the rows or cols.
		To simplify things we test the current input pixel position to see wether it is
		in bounds, if not, we run a simplified version of the code to keep track of the rates
		but we set all the input pixels to a negative value (transparent) */
	
	sS = minRow*IT4 + IT6;
	for(r=minRow;r<maxRow;r++) {

		float accumulator = 0.0;
		float inputPixel = 0.0;
		
		iS = (1.0 - ( sS - (int)sS ) );
		oS = IT5;
		
		int im1p = sS;
		
		for ( c=0; c<=destinationCols-1; ) {
			if ( im1p < 0 || im1p >= sourceCols-1 ) {
				if ( iS <= oS ) {
					oS = oS - iS;
					im1p++;
					iS = 1.0;
				} else {
					iS = iS - oS;
					oS = IT5;
					b1[r][c++] = -10000;
				}
			} else {
				inputPixel = p1[r][im1p]*iS + p1[r][im1p+1]*(1-iS);
				if ( iS <= oS ) {
					oS = oS - iS;
					accumulator += inputPixel * iS;
					im1p++;
					iS = 1.0;
				} else {
					accumulator += inputPixel * oS;
					iS = iS - oS;
					oS = IT5;
					b1[r][c++] = accumulator * TR5;
					accumulator = 0.0;
				}
			}
		}
		
		sS += IT4;
		
	}
		
	for(sS=IT3,c=0;c<destinationCols;c++) {
		
		float accumulator = 0.0;
		float inputPixel = 0.0;
		
		iS = (1.0 - ( sS - (int)sS ) );
		oS = IT1;

		int im1p = sS;

		for ( r=0;r<=destinationRows-1; ) {
			if ( im1p < 0 || im1p >= sourceRows-1 ) {
				if ( iS <= oS ) {
					oS = oS - iS;
					im1p++;
					iS = 1.0;
				} else {
					iS = iS - oS;
					oS = IT1;
					p2[r++][c] = -10000;
				}
			} else {
				inputPixel = b1[im1p][c]*iS + b1[im1p+1][c]*(1-iS);
				if ( iS <= oS ) {
					oS = oS - iS;
					accumulator += inputPixel * iS;
					im1p++;
					iS = 1.0;
				} else {
					accumulator += inputPixel * oS;
					iS = iS - oS;
					oS = IT1;
					p2[r++][c] = accumulator * TR1;
					accumulator = 0.0;
				}
			}
		}
		
		sS += IT2;
		
	}
	
	
}

Image SubtractImages( Image im1, Image im2, Image im3 ) {
	int maxr = MIN(im1->rows,im2->rows);
	int maxc = MIN(im1->cols,im2->cols);
	if ( im3 == NULL ) im3 = CreateImage(maxr,maxc);
	maxr = MIN(maxr,im3->rows);
	maxc = MIN(maxc,im3->cols);
	int minv = MIN(im1->minv,im2->minv);
	int maxv = MAX(im1->maxv,im2->maxv);
	int r, c;
	for (r=0;r<maxr;r++) {
		for (c=0;c<maxc;c++) {
			int pix = im1->pixels[r][c] - im2->pixels[r][c];
			pix = BOUND(minv,pix,maxv);
			im3->pixels[r][c] = pix;
	}}
	
	return im3;
	
}

Image MultiplyImages( Image im1, Image im2, Image im3 ) {
	int maxr = MIN(im1->rows,im2->rows);
	int maxc = MIN(im1->cols,im2->cols);
	if ( im3 == NULL ) im3 = CreateImage(maxr,maxc);
	maxr = MIN(maxr,im3->rows);
	maxc = MIN(maxc,im3->cols);
	int minv = MIN(im1->minv,im2->minv);
	int maxv = MAX(im1->maxv,im2->maxv);
	int r,c;
	for (r=0;r<maxr;r++) {
		for (c=0;c<maxc;c++) {
			int pix = im1->pixels[r][c] * ((float)im2->pixels[r][c]/maxv);
			pix = BOUND(minv,pix,maxv);
			im3->pixels[r][c] = pix;
	}}
	
	return im3;
}

Image UnsharpMaskImage( Image im, float sigma ) {
	if ( sigma <= 0.0 ) return im;
	Image copy = GaussianBlurImage(CopyImage(im),sigma);
	copy = SubtractImages( im, copy, copy );
	im = SubtractImages( im, copy, im );
	FreeImage(copy);
	return im;
	
}

char RowColWithinImage( Image image, int row, int col ) {
	if ( row < 0 ) return FALSE;
	if ( col < 0 ) return FALSE;
	if ( row >= image->rows ) return FALSE;
	if ( col >= image->cols ) return FALSE;
	return TRUE;
}

void PasteImage( Image clip, Image targ, int row, int col ) {
	int r, c;
	for (r=0;r<clip->rows;r++) {
		for (c=0;c<clip->cols;c++) {
			int tr = row + r;
			int tc = col + c;
			if ( tr < 0 || tc < 0 ) continue;
			if ( tr >= targ->rows || tc >= targ->cols ) continue;
			targ->pixels[tr][tc] = clip->pixels[r][c];
	}}
}

int RandomColor( int lum ) {
	int rv = RandomNumber(0,255);
	int gv = RandomNumber(0,255);
	int bv = RandomNumber(0,255);
	if ( rv < lum && gv < lum && bv < lum ) { rv += lum; gv += lum; bv += lum; }
	return (PIX3(rv,gv,bv));
}
