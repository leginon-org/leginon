#ifndef _EDGE_H#define _EDGE_Hclass Node;class Edge{	public:		Edge( Node *, Node * );		void addImage( Node *, float * );		void incAge( );		void resetAge( );
		int getAge( ) { return age; }
		bool isTooOld( ) { return age >= maxAge; } 		bool exists( Node * );
		float getError( Node * );
		float * getLoc( Node * );
		void decreaseError( Node *, float );
		void makeConnection( Node *, Node * );
		void eraseEdge( Node * );
		int getGridX( Node * );
		int getGridY( Node * );
		bool isConnectedTo( Node *, Node * );

		void tellNeighborNULL( Node * );

		static int maxAge;				private:    		int age;		Node * first;		Node * second;
		Node * figurePolarity( Node * );				};#endif

