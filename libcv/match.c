#include "match.h"
#include "lautil.h"

/* Local Function Prototypes */
void FindMatch( Descriptor d1, PStack d2s, int bound, PStack );
float DistSquared( float *d1, float *d2);

void freeMatches( PStack matches ) {
	
	while ( !PStackIsEmpty(matches) ) free(PopPStack(matches));
		
}

void FindMatches(PStack d1s, PStack d2s, PStack matches, int bound ) {	
	int k;
	int size = d1s->stacksize;
	for (k=0;k<size;k++) {	
		Descriptor d1 = d1s->items[k];
		FindMatch( d1, d2s, bound, matches );
	}
}

void FindMatch( Descriptor d1, PStack d2s, int bound, PStack matches ) {
	
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
    
	if ( distsq1*bound*bound >= distsq2*(bound-1)*(bound-1) ) return;

	Match match = malloc(sizeof(struct MatchSt));
   match->p1 = d1;
	match->p2 = dbest;
	match->score = distsq1;
	PushPStack(matches,match);

}

float FindArea( FArray array ) {
	/* Points must be given in the order in which they form
		the polygon.  Order does not matter for triangles. */
	if ( FArrayRows(array) < 3 ) return 0;
	int i;
	float **p = array->values, area = 0;
	int minr = array->minrow;
	int maxr = array->maxrow;
	int minc = array->mincol;
	int maxc = array->maxcol;
	for (i=minr+1;i+1<=maxr;i++) {
		int y1 = p[i][minc] - p[minr][minc];
		int x1 = p[i][maxc] - p[minr][maxc];
		int y2 = p[i+1][minc] - p[minr][minc];
		int x2 = p[i+1][maxc] - p[minr][maxc];
		area += x1*y2 - x2*y1;
	}
	return ABS(area)/2;
}

void CreateAffineTransform( FArray PO, double **TR );
void CreateAffineTransform( FArray PO, double **TR ) {
	
	float **ar = PO->values;
	
	if ( FArrayRows(PO) == 3 ) 
		CreateDirectAffineTransform(ar[0][0],ar[0][1],ar[1][0],ar[1][1],ar[2][0],ar[2][1],ar[0][2],ar[0][3],ar[1][2],ar[1][3],ar[2][2],ar[2][3],TR,NULL);
	else FatalError("CreateAffineTransform: Least Squares fitting not yet implimented.\n");
}

//int TransformGood( double **TR );
int TransformGood( double **TR ) {
	//return TRUE;
	/* This verifies that tranform does not compress everything
		into a single line. */
		
	//if ( TR[0][0] == 0.0 && TR[1][0] == 0.0 ) return FALSE;
	//if ( TR[1][0] == 0.0 && TR[1][1] == 0.0 ) return FALSE;
	
	/* This verifies that the tranform does not contain NaN values
		since a property of NaN is NaN != NaN */
		
	if ( TR[0][0] != TR[0][0] ) return FALSE;
	//if ( TR[0][1] != TR[0][1] ) return FALSE;
	//if ( TR[0][2] != TR[0][2] ) return FALSE;
	//if ( TR[1][0] != TR[1][0] ) return FALSE;
	//if ( TR[1][1] != TR[1][1] ) return FALSE;
	//if ( TR[1][2] != TR[1][2] ) return FALSE;
	//if ( TR[2][0] != TR[2][0] ) return FALSE;
	//if ( TR[2][1] != TR[2][1] ) return FALSE;
	//if ( TR[2][2] != TR[2][2] ) return FALSE;
	
	/* Neil extra testing */
	//max tilt angle of 73 degrees, ang ~= arccos(t)
	if (fabs(TR[0][0]) < 0.5) return FALSE; 
	if (fabs(TR[1][1]) < 0.5) return FALSE;
	//only allow 71 degrees of expansion, ang ~= arccos(1/t)
	if (fabs(TR[0][0]) > 1.4) return FALSE; 
	if (fabs(TR[1][1]) > 1.4) return FALSE;
	// max rotation angle of 65 degrees, ang ~= arcsin(t)
	if (fabs(TR[0][1]) > 0.8) return FALSE; 
	if (fabs(TR[1][0]) > 0.8) return FALSE; 
	// max shift of 250 pixels
	//if (fabs(TR[2][1]) > 200) return FALSE; 
	//if (fabs(TR[2][0]) > 200) return FALSE; 

	/* FORM of MATRIX
		[	math.cos(radangle)**2 + math.sin(radangle)**2/math.cos(raddifftilt),
			(1.0-1.0/math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
			0.0
		], 
		[	(1.0-1.0/math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
			math.sin(radangle)**2 + math.cos(radangle)**2/math.cos(raddifftilt),
			0.0
		], 
		[shift[0], shift[1], 0.0]], 
	*/

	/* We have a reasonable tranform */
	
	return TRUE;
	
}

void ScreenMatches( PStack matches, double **transform ) {
	
	float pgood = 0.95;
	float pfail = 0.001;
	int points  = 3;
	float treshold = 2;
	int largest  = 1;
	int j;
	int goodpoints;
	unsigned long i, max, L;
	FArray fr = NewFArray(0,0,2,3);

	int numberofmatches = matches->stacksize-1;
	
	if ( numberofmatches < 5 ) {
		fprintf(stderr,"Not enough matches\n");
		return;
	}
	
	double **tbest = AllocDMatrix(3,3,0,0);

	L = (long) ceil((log(pfail))/(log(1-(pow(pgood,points)))));
	max = (long) ceil((log(pfail))/(log(1-(pow(((float)points/numberofmatches),points)))));
	//fprintf(stderr,"Max RANSAC iters %ld\n",max);

	for (i=1; i != max; i++) {
		
		ResizeFArray(fr,0,0,2,3);
		for (j=0;j<3;j++) {
			int entry = RandomNumber(0,numberofmatches);
			Match match = matches->items[entry];
			SetFArray(fr,j,0,match->p1->row);
			SetFArray(fr,j,1,match->p1->col);
			SetFArray(fr,j,2,match->p2->row);
			SetFArray(fr,j,3,match->p2->col);
		}
		
		if ( FindArea(ResizeFArray(fr,0,0,2,1)) < 100 ) continue;
		if ( FindArea(ResizeFArray(fr,0,2,2,3)) < 100 ) continue;
		
		CreateAffineTransform(ResizeFArray(fr,0,0,2,3),transform);
		if ( !TransformGood(transform) ) continue;

		goodpoints=0;
		
		for  ( j=0;j<=numberofmatches;j++ ) {	
			Match match = matches->items[j];	
			float row1 = match->p1->row;
			float col1 = match->p1->col;

			float row2 = row1*transform[0][0]+col1*transform[1][0]+transform[2][0];
			float col2 = row1*transform[0][1]+col1*transform[1][1]+transform[2][1];
			
			row1 = match->p2->row;
			col1 = match->p2->col;
			
			float dist = (row2-row1)*(row2-row1)+(col2-col1)*(col2-col1);
			
			if ( dist < treshold ) goodpoints++;
			//if ( dist < treshold ) goodpoints+=1.0/(dist*dist+1.0);
			
		}
				

		if ( goodpoints > largest ) {
			largest = goodpoints;
			CopyDMatrix(transform,tbest,0,0,2,2);
		}

		if ( i >= L ) {
			pgood = pgood - 0.05;
			L = (int) ceil((log(pfail))/(log(1-(pow(pgood,points)))));
		}
		
		if (largest > pgood*numberofmatches) {
			
			fprintf(stderr,"Found matrix that fit %d out of the %d matches.\n",largest,numberofmatches);
			CopyDMatrix(tbest,transform,0,0,2,2);

			FreeDMatrix(tbest,0,0);
			FreeFArray(fr);
			return;
		}
		
	}
	
	fprintf(stderr, "\nRANSAC failed, returning best match at %d.\n", largest);
	FreeDMatrix(tbest,0,0);
	FreeFArray(fr);
	return;
}

