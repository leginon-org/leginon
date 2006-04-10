#include "defs.h"


void DrawPixelArray( FArray array, PPMImage out, int r, int g, int b ) {
	
	if ( array = NULL || out == NULL ) return;
	
	int i;
	int minr = array->minrow;
	int minc = array->mincol;
	int maxr = array->maxrow;
	int maxc = array->maxcol;
	
	int maxrow = out->rows;
	int maxcol = out->cols;
	
	for (i=minc;i<=maxc;i++) {
		int row = array->values[minr][i];
		int col = array->values[maxr][i];
		if (row<0||row>maxrow-1||col<0||col>maxcol-1) continue;
		out->red[row][col]   = r;
		out->green[row][col] = g;
		out->blue[row][col]  = b;
	}
	
}

void DrawEllipse( Ellipse e, PPMImage out, int r, int g, int b ) {

	if ( e == NULL || out == NULL ) return;
	
	int maxrow = out->rows;
	int maxcol = out->cols;
	
	float maj = e->majaxis;
	float min = e->minaxis;
	
	float c = cos(e->phi);
	float s = sin(e->phi);
	
	int erow = e->erow;
	int ecol = e->ecol;
	
	float rowc =  erow*c + ecol*s;
	float colc = -erow*s + ecol*c;
	
	float pixdist = 4/maj;
	
	int row, col;
	for(row=erow-maj;row<=erow+maj;row++) {
		for(col=ecol-maj;col<=ecol+maj;col++) {
			if ( row < 0 || col < 0 || row > maxrow-1 || col > maxcol -1 ) continue;
			float mrow = row*c + col*s;
			float mcol = -row*s + col*c;
			float aa = (rowc-mrow)/maj;
			float bb = (colc-mcol)/min;
			float val = aa*aa + bb*bb;
			
			if ( val <= 1.0 && val >= 1-pixdist ) {
				out->green[row][col] = g;
				out->red[row][col]   = r;
				out->blue[row][col]  = b;
			}
	}}
	
}

void FastLineDraw(int srow, int scol, int erow, int ecol, PPMImage out, int r, int g, int b ) {
	
	
	int maxcol = out->cols;
	int *red   = out->red[0];
	int *blue  = out->blue[0];
	int *green = out->green[0];

	int x0 = scol;
	int y0 = srow;
	int x1 = erow;
	int y1 = ecol;
	
	int dy = y1 - y0;
	int dx = x1 - x0;
	int stepx, stepy;
	
    if (dy < 0) { dy = -dy;  stepy = -maxcol; } else { stepy = maxcol; }
    if (dx < 0) { dx = -dx;  stepx = -1; } else { stepx = 1; }
	dy <<= 1;
	dx <<= 1;

	y0 *= maxcol;
	y1 *= maxcol;
	pixels[x0+y0] = 255;
	if (dx > dy) {
		int fraction = dy - (dx >> 1);
		while (x0 != x1) {
			if (fraction >= 0) {
				y0 += stepy;
				fraction -= dx;
			}
			x0 += stepx;
			fraction += dy;
			red[x0+y0] = r;
			green[x0+y0] = g;
			blue[x0+y0] = b;
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
			red[x0+y0] = r;
			green[x0+y0] = g;
			blue[x0+y0] = b;
		}
	}
}

