
#include "Edge.h"
#include "Node.h"
#include <iostream>

using namespace std;

int Edge::maxAge = 0;

Edge::Edge( Node * f, Node * s )
{
	first = f;
	second = s;
	age = 1;
    
}


void Edge::addImage( Node * t, float * im )
{
	Node * temp = figurePolarity( t );
	temp->addImage( im );	
}

void Edge::incAge( )
{
	age ++;
}


void Edge::resetAge( )
{
    age = 1;
    
}

bool Edge::exists( Node * n )
{
	if(first == n || second == n)
	{
		return true;
	}
	else
	    return false;
}

Node * Edge::figurePolarity( Node * n )
{
	if( n == first ) {
	    return second;
	} else if( n == second ){
	    return first;
	} else {
	    cout<<"error assigning directionality at edge!"<<endl;
	    return NULL;
	}

	return NULL;
}

float Edge::getError( Node *n )
{
	Node *temp = figurePolarity( n );
	return temp->getError( );
}

float * Edge::getLoc( Node *n )
{
	Node *temp = figurePolarity( n );
	return temp->getLoc( );
}

void Edge::decreaseError( Node *n, float f )
{
	Node *temp = figurePolarity( n );
	temp->decreaseError( f );
}

void Edge::makeConnection( Node *n, Node *newNode )
{
	Node *temp = figurePolarity( n );
	temp->makeEdge( newNode );
}

void Edge::eraseEdge( Node *n )
{
	Node *temp = figurePolarity( n );
	temp->eraseEdge( this );
}

int Edge::getGridX( Node *n )
{
	Node *temp = figurePolarity( n );
	return temp->getGridX();
}

int Edge::getGridY( Node *n )
{
	Node *temp = figurePolarity( n );
	return temp->getGridY();
}

void Edge::tellNeighborNULL( Node * n )
{
	Node *temp = figurePolarity( n );
	temp->setEdgeNULL( this );
}

bool Edge::isConnectedTo( Node * n, Node * neighbor)
{
	bool isConnected = false;
	Node *temp = figurePolarity( n );
	if( temp == neighbor )
	{
		isConnected = true;
	}

	return isConnected;

}


