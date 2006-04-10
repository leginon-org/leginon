#include "defs.h"
#include "lautil.h"

/* Local Function Prototypes */
Descriptor FindMatch( Descriptor d1, PStack d2s, int bound );
float DistSquared( float *d1, float *d2);

void FindMatches(PStack d1s, PStack d2s, PStack matches, int bound ) {	
	int k;
	int size = d1s->stacksize;
	for (k=0;k<size;k++) {	
		Descriptor d1 = d1s->items[k];
		Descriptor d2 = FindMatch( d1, d2s, bound );
		if ( d1 == NULL || d2 == NULL ) continue;
		Match match = malloc(sizeof(struct MatchSt));
		match->p1 = d1;
		match->p2 = d2;
		PushPStack(matches, match);
	}
}

Descriptor FindMatch( Descriptor d1, PStack d2s, int bound ) {
	
    float distsq1 = 1000000000, distsq2 = 1000000000;
	Descriptor d2 = NULL, dbest = NULL;
	
	int k;
	int size = d2s->stacksize;
    for (k=0;k<size;k++) {
		d2 = d2s->items[k];
		if ( d1->descriptortype != d2->descriptortype ) continue;
		if ( d1->descriptorlength != d2->descriptorlength ) continue;
		float dist = VDISTSQ(d1->descriptor, d2->descriptor, 0, d1->descriptorlength-1);
		if (dist<0) continue; 
		if (dist < distsq1) {
			distsq2 = distsq1;
			distsq1 = dist;
			dbest = d2;
		} else if (dist < distsq2) {
			distsq2 = dist;
		}
    }
    
	if ( distsq1*bound*bound >= distsq2*(bound-1)*(bound-1) ) return NULL;
	return dbest;
   
}

int FindArea( PointStack points ) {
	/* Points must be given in the order in which they form
		the polygon.  Order does not matter for triangles. */
	if (points->stacksize<3) return 0;
	int i, area = 0;
	Point p = points->items;
	int stacksize = points->stacksize;
	for (i=1;i+1<stacksize;i++) {
		int y1 = p[i].row - p[0].row;
		int x1 = p[i].col - p[0].col;
		int y2 = p[i+1].row - p[0].row;
		int x2 = p[i+1].col - p[0].col;
		area += x1*y2 - x2*y1;
	}
	return ABS(area)/2;
}

void CreateAffineTransform( PointStack from, PointStack to, double **TR );
void CreateAffineTransform( PointStack from, PointStack to, double **TR ) {
	
	float x1,y1,x2,y2,x3,y3,x4,y4,x5,y5,x6,y6;
	Point p;
	
	p = PopPointStack(from);
	x1 = p->row;
	y1 = p->col;
	p = PopPointStack(from);
	x2 = p->row;
	y2 = p->col;
	p = PopPointStack(from);
	x3 = p->row;
	y3 = p->col;
	p = PopPointStack(to);
	x4 = p->row;
	y4 = p->col;
	p = PopPointStack(to);
	x5 = p->row;
	y5 = p->col;
	p = PopPointStack(to);
	x6 = p->row;
	y6 = p->col;
	
	CreateDirectAffineTransform(x1,y1,x2,y2,x3,y3,x4,y4,x5,y5,x6,y6,TR,NULL);
}

int ValidateTransform( double **TR );
int ValidateTransform( double **TR ) {
	
	if ( TR[0][0] != TR[0][0] ) return 0;
	if ( TR[0][1] != TR[0][1] ) return 0;
	if ( TR[0][2] != TR[0][2] ) return 0;
	if ( TR[1][0] != TR[1][0] ) return 0;
	if ( TR[1][1] != TR[1][1] ) return 0;
	if ( TR[1][2] != TR[1][2] ) return 0;
	if ( TR[2][0] != TR[2][0] ) return 0;
	if ( TR[2][1] != TR[2][1] ) return 0;
	if ( TR[2][2] != TR[2][2] ) return 0;
	
	return 1;
	
}
	
void ScreenMatches( PStack matches, double **transform ) {
	
	float pgood = 0.95;
	float pfail = 0.001;
	int points = 3;
	int treshold = 1;
	int largest = 1;
	int j, goodpoints;
	unsigned long i, max, L;
	PointStack from = NewPointStack(3);
	PointStack to   = NewPointStack(3);

	int numberofmatches = matches->stacksize-1;
	
	double **tbest = AllocDMatrix(3,3,0,0);
	
	L = (long) ceil((log(pfail))/(log(1-(pow(pgood,points)))));
	max = (long) ceil((log(pfail))/(log(1-(pow(((float)points/numberofmatches),points)))));
	
	for (i=1; i != max; i++) {
	
		for (j=0;j<3;j++) {
			int entry = randomnumber()*numberofmatches;
			Match match = matches->items[entry];
			PushPointStack( from, match->p1->row, match->p1->col );
			PushPointStack( to  , match->p2->row, match->p2->col );
		}
	
		if ( FindArea(from) < 100 ) continue;
		if ( FindArea(to) < 100 ) continue;
		
		CreateAffineTransform(from,to,transform);
		if ( !ValidateTransform(transform) ) continue;

		goodpoints=0;
		for (j=0;j<=numberofmatches;j++) {	
			Match match = matches->items[j];	
			float row1 = match->p1->row;
			float col1 = match->p1->col;
			float row2 = match->p2->row;
			float col2 = match->p2->col;
							
			float row = row1*transform[0][0]+col1*transform[1][0]+transform[2][0];
			float col = row1*transform[0][1]+col1*transform[1][1]+transform[2][1];

			float dist = (row2-row)*(row2-row)+(col2-col)*(col2-col);
			
			if (dist<treshold) goodpoints++;
			
			if (goodpoints > largest) {
				largest = goodpoints;
				CopyDMatrix(transform,tbest,0,0,2,2);
			}
		}

		if ( i >= L ) {
			pgood = pgood - 0.01;
			L = (int) ceil((log(pfail))/(log(1-(pow(pgood,points)))));
		}
		
		if (largest > pgood*numberofmatches) {
			fprintf(stderr,"%lf %lf %lf\n",tbest[0][0],tbest[0][1],tbest[0][2]);
			fprintf(stderr,"Found matrix that fit %d out of the %d matches.\n",largest,numberofmatches);
			CopyDMatrix(tbest,transform,0,0,2,2);
			
			FreeDMatrix(tbest,0,0);
			FreePointStack(from);
			FreePointStack(to);
			return;
		}
		
	}
	
	fprintf(stderr, "\nRANSAC failed, returning best match at %d.\n", largest);
	FreeDMatrix(tbest,0,0);
	FreePointStack(from);
	FreePointStack(to);
	return;
}

