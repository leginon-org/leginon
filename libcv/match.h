
#ifndef libCV_match
#define libCV_match

#include "geometry.h"
#include "csift.h"

typedef struct MatchSt {
	struct DescriptorSt *p1, *p2;
	float score;
} *Match;


void FindMatches(PStack k1, PStack k2, PStack matches, int bound );
float FindArea( FArray array );
void ScreenMatches( PStack matches, double **transform);
void freeMatches( PStack matches );

#endif
