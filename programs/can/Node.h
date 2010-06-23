/*
 *  Node.h
 *  
 *
 *  Created by Vincent Ramey on 8/10/06.
 *  Copyright 2006 __MyCompanyName__. All rights reserved.
 *
 */

class Node;

#include "Edge.h"
#include <vector>

using namespace std;


class Node
{
	public:
		Node( float *location, float error );
		~Node();
		
		float checkDist( float *part_loc );
		void moveToward( float *loc );
		void addImage( float *loc );
		float * getLoc( ) {
		    return myLocation;
		}
		float * getAvgLoc( );
		void addToAvg( float *, int );
		void calcAvg( );
		vector<int> * getParts( ) { return & particles; }
		
		void addError( float e ) { myError += e; }
		float getError( ) { return myError; }
		void decreaseError( float fac ) { myError *= fac; }
		
		void makeEdge( Node * );
		void receiveEdge( Edge * );
		void eraseEdge( Edge * );
		bool isConnectedTo( Node * );
		int getNumEdges( ) { return edges.size(); }
		float getTotEdgeAge( );
		void setEdgeNULL( Edge * );
		void deleteEdges( );

		Node * makeNode( );
	
		//GRID FUNCTIONS
		void setGridLoc( int x, int y ) { gridX = x; gridY = y; }
		int getGridX( ) { return gridX; }
		int getGridY( ) { return gridY; }
		float getGridDistFromNeighbors( );
		/////////////////

		static float primLearn;
		static float secLearn;
		static float alpha;
		
		static void setDim( int d ) {
		    dim = d; 
		}

		static int getDim( ) { return dim; }
		
		
	private:
		float *myLocation;
		float *myAvgLocation;
		int myAvgImgNum;
		static int dim;
		
		float myError;
		vector< Edge * > edges;
		vector< int > particles;

		int gridX;
		int gridY;
	
};
