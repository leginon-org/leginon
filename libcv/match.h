typedef struct MatchSt {
	struct DescriptorSt *p1, *p2;
} *Match;


/*-------------------------- Function prototypes -------------------------*/



void FindMatches(PStack k1, PStack k2, PStack matches, int bound );
int FindArea( PointStack points );
void ScreenMatches( PStack matches, double **transform);
