/*
 *  Node.cpp
 *  
 *
 *  Created by Vincent Ramey on 8/10/06.
 *  Copyright 2006 __MyCompanyName__. All rights reserved.
 *
 */

#include "Node.h"

#include <iostream>

using namespace std;

int Node::dim = 0;
float Node::secLearn = 0;
float Node::primLearn = 0;
float Node::alpha = 0;


Node::Node( float *location, float error )
{
	myLocation = new float[dim];
	myAvgLocation = new float[dim];

	for(int i = 0; i < dim; i++)
	{
		myLocation[i] = location[i];
		myAvgLocation[i] = 0;
	}
	
	myError = error;
	myAvgImgNum = 0;
}

Node::~Node( )
{
	delete myLocation;
	delete myAvgLocation;
	for( int i = 0; i < edges.size(); i++)
	{
		if( edges[i] != NULL )
		{
			delete edges[i];
			edges[i] = NULL;
		}
	}

	edges.clear();
	particles.clear();
}

void Node::deleteEdges( )
{
	for( int i = 0; i < edges.size(); i++ )
	{
		if( edges[i] == NULL )
		{
			continue;
		}

		edges[i]->tellNeighborNULL( this );
		delete edges[i];
		edges[i] = NULL;
	}
}

void Node::makeEdge( Node * n )
{
    for(int i = 0; i < edges.size(); i++)
    {
        if( edges[i]->exists( n ) )
	 {
	     	edges[i]->resetAge();
	 	return;
	 }
    }

    Edge * e = new Edge( this, n );
    
    edges.push_back( e );
    
    n->receiveEdge( e );
    
}

void Node::receiveEdge( Edge * e )
{
    edges.push_back( e );
    
}



float Node::checkDist( float *location )
{
	float cumError = 0;
	float temp = 0;

	for(int i = 0; i < dim; i++)
	{
		temp = location[i] - myLocation[i];  //find distance in dimension i
		cumError += (temp * temp);  //add squared dist from dimension i
	}
	
	return cumError;

}

void Node::moveToward( float *loc )
{
	for(int i = 0; i < dim; i ++)
	{
		myLocation[i] = myLocation[i] + primLearn*(loc[i] - myLocation[i]);
	}
	
	for(int i = 0; i < edges.size(); i++)
	{
		edges[i]->addImage( this, loc );
		edges[i]->incAge();
	}
	for(int i = 0; i < edges.size(); i++)
	{
		if( edges[i]->isTooOld( ) )
		{
			edges[i]->eraseEdge( this );
			delete edges[i];
			edges.erase( edges.begin() + i );
			i = -1;
		}
	}
}

void Node::addImage( float *loc )
{
    for(int i = 0; i < dim; i ++)
    {
	    myLocation[i] = myLocation[i] + secLearn*(loc[i] - myLocation[i]);
    }    
}

Node * Node::makeNode( )
{
	float topError = -1000;
	int topInd = -1;

	for( int i = 0; i < edges.size(); i++ )
	{
		if( topError < edges[i]->getError( this ) )
		{
			topError = edges[i]->getError( this );
			topInd = i;
		}				
	}//find neighboring node with highest error to place new node

	if( topInd == -1 || edges.size() == 0 )
	{
		cout<<"error finding place for new node...  recalculating..."<<endl;
		return NULL;
	}

	float * neighborLoc = edges[topInd]->getLoc( this );

	float * newLoc = new float[dim];
	for( int i = 0; i < dim; i++ )
	{
		newLoc[i] = .5*(neighborLoc[i] + myLocation[i]);
	}

	myError *= alpha; //decrease the error here since adding a new node
	edges[topInd]->decreaseError( this, alpha );

	Node * newNode = new Node( newLoc, myError ); //make new node

	edges[topInd]->makeConnection( this, newNode ); //make connections between the "parents" and newNode
	makeEdge( newNode );

	edges[topInd]->eraseEdge( this );
	delete edges[topInd];
	edges.erase( edges.begin() + topInd );

	return newNode;

}

void Node::eraseEdge( Edge * e )
{
	bool erased = false;

	for(int i = 0; i < edges.size(); i++)
	{
		if( edges[i] == e )
		{
			//cout<<edges.size()<<" edges exist... ";
			edges.erase( edges.begin() + i );
			erased = true;
			//cout<<"erasing edge...  "<<edges.size()<<" edges left..."<<endl;
			break;
		}
	}

	if( !erased )
		cout<<"edge to be erased was not found!  Something may be afoot!"<<endl;

}

float Node::getTotEdgeAge( )
{
	float totAge = 0;
	for( int i = 0; i < edges.size(); i++ )
	{
		totAge += edges[i]->getAge( );
	}
	return totAge;
}

float Node::getGridDistFromNeighbors( )
{
	float totalDist = 0;
	int tempX = 0;
	int tempY = 0;
	int dX = 0;
	int dY = 0;

	for( int i = 0; i < edges.size(); i++ )
	{
		tempX = edges[i]->getGridX( this );
		tempY = edges[i]->getGridY( this );
		dX = gridX - tempX;
		dY = gridY - tempY;
		totalDist += (dX * dX) + (dY * dY);
	}

	return totalDist;

}

void Node::calcAvg()
{
	if( myAvgImgNum == 0 )
	{
		return;
	}

	for( int i = 0; i < dim; i++ )
	{
		myAvgLocation[i] /= myAvgImgNum;
	}
}

float * Node::getAvgLoc( )
{
	return myAvgLocation;
}

void Node::addToAvg( float * img, int index )
{

	for( int i = 0; i < dim; i ++)
	{
		myAvgLocation[i] += img[i];
	}

	myAvgImgNum++;

	particles.push_back( index );

}

void Node::setEdgeNULL( Edge * e )
{

	for( int i = 0; i < edges.size(); i++)
	{
		if( edges[i] == e )
		{
			edges[i] = NULL;
		}
	}
}

bool Node::isConnectedTo( Node * n )
{
	bool isConnect = false;

	for( int i = 0; i < edges.size(); i++ )
	{
		if( edges[i]->isConnectedTo( this, n ) )
		{
			isConnect = true;
			break;
		}		
	}

	return isConnect;

}




