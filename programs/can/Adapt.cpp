


#include <iostream>
#include <cstring>
#include <cstdio>
#include "imagic.h"
#include "Node.h"
#include <vector>
#include <cstdlib>
#include <ctime>
#include <cmath>
#include <fstream>

using namespace std;


#define FLOAT_SIZE	4
#define D_ERROR_FACTOR	.995  //decrease error of all Node by this factor each iteration
#define LAMBDA_DECAY	1     //factor to slow decrease of learning rate (1 is no change) higher -> slower
#define GRID_SIZE	50
#define ANNEAL_ITER	200000
#define TIME_CONSTANT	20000
#define DELTA_RANGE	41
#define INIT_TEMP	20000
#define SA_UNIT_WEIGHT	5000000
#define SA_EDGE_WEIGHT	1000
#define ADD_SPEED_FACTOR	1 // this changes the way the nodes are added.  When 2, all nodes are added by the
				  // midpoint of the run

void addNoise( float*, int );
float calcEnergy( Node ***, vector<Node *> * );
float getGaussianRand( float sigma );

int main( int argc, char **argv )
{
  
	/////USEAGE STATEMENT HERE  


	if( argc != 8 )
	{
		cout<<"usage : "<<argv[0]<<" <input imagic stack> <output imagic stack> <# of iterations> ";
		cout<<"<direct learning rate> <indirect learning rate> <max age> <total # of nodes in network>"<<endl<<endl<<endl<<endl;
		cout<<"<input imagic stack> : imagic format file for classification (usually output of an MRA)"<<endl<<endl;
		cout<<"<output imagic stack> : output file name for the classification images (unit images not averages!)"<<endl<<endl;
		cout<<"<# of iterations> : number of times data will be presented to the network.  This number"<<endl;
		cout<<"should be ~15 or more times greater than your number of particles in <input imagic stack>"<<endl<<endl;
		cout<<"<direct learning rate> : fraction that closest unit image will be moved toward presented data (paper suggests .01 for cryoEM, higher for neg stain?  EXPERIMENT!)"<<endl<<endl;
		cout<<"<indirect learning rate> : fraction that connection unit images will be moved (same advice as above! except .0005 is recommended - should be lower than direct rate)"<<endl<<endl;
		cout<<"<max age> : number of iterations an edge connecting two units can be unused before it's discarded (paper suggests 30-40, experiment with this too!  I've found ~20 gives better sampling of all views)"<<endl<<endl;
		cout<<"<total # of nodes in network> : should be on the order of 20 times less than particle number"<<endl<<endl;

		cout<<"*********Implementation of 'Topology representing network enables highly accurate classification of protein images taken by cryo electron-microscope without masking' by Ogura, Iwasaki and Sato (2003) J. Struct. Bio."<<endl;
		exit(1);
		
	}
	
	char filename[256];	// = "test_file";
	strcpy( filename, argv[1] );
	
	char outfile[256];	//	= "tempOutput";
	strcpy( outfile, argv[2] );
	
	//int inDim = atoi( argv[3] );
	
	int numPres = atoi( argv[3] );
	
	float eb = atof( argv[4] );
	
	float en = atof( argv[5] );

	int maxAge = atoi( argv[6] );

	int maxNodes = atoi( argv[7] );

	cout<<"maxNodes = "<<maxNodes<<endl;

	int addInterval = numPres / maxNodes / ADD_SPEED_FACTOR; //number of iterations between adding new nodes
	
	
	//INITALIZE STATIC MEMBERS
	//Node::setDim( inDim );
	Node::secLearn = en;
	Node::primLearn = eb;
	Node::alpha = .5;
	Edge::maxAge = maxAge;
	
	
	//Initialize rand
	srand( time(NULL) );
	
	
	// READ IN IMAGES

	char filename_hed[256];
	char filename_img[256];

	strcpy(filename_hed, filename);  // make names for both .hed
	strcpy(filename_img, filename);  // and .img imagic files

	strcat(filename_hed, ".hed");
	strcat(filename_img, ".img");


	FILE *stack_hed, *stack_img ;
	imagicH *iHeader = new imagicH;
	stack_hed = fopen( filename_hed, "rb" );

	if( stack_hed == NULL )
	{
		cout<<"error opening imagic file "<<filename_hed<<"  !  Exiting..."<<endl;
		exit(10);
	}

	fread(iHeader,4,256,stack_hed);	//Fill header struct with data from first image
	rewind(stack_hed);

	iHeader->count++;

	int imageCount = iHeader->count;

	cout<<"DIAGNOSTIC FILE INFO"<<endl;
	cout<<"pixels = "<<iHeader->pixels<<endl;
	cout<<"count = "<<iHeader->count<<endl;
	cout<<"reals = "<<iHeader->reals<<endl;
	cout<<"headrec = "<<iHeader->headrec<<endl;
	cout<<"cellx = "<<iHeader->cellx<<endl;
	cout<<"celly = "<<iHeader->celly<<endl;
	cout<<"cellz = "<<iHeader->cellz<<endl;
	cout<<"nx = "<<iHeader->nx<<endl;
	cout<<"ny = "<<iHeader->ny<<endl;

	if( iHeader->pixels == 0 )
	{
		cout<<"pixel count in header = 0!  Setting to nx * ny!"<<endl;
		iHeader->pixels = iHeader->nx * iHeader->ny;
	}

	Node::setDim( iHeader->pixels ); // set dimensionality from file info
	
	stack_img  = fopen( filename_img, "rb" );

	if( stack_img == NULL )
	{
		cout<<"error opening imagic file "<<filename_img<<"  !  Exiting..."<<endl;
		exit(11);
	}

	////ALLOCATE IMAGE DATA STORAGE

	float **image_data = new float * [iHeader->count];

	for(int i = 0; i < iHeader->count; i++)
	{
		image_data[i] = new float[iHeader->pixels];
	}

	int byteSize = FLOAT_SIZE*iHeader->pixels;
	
	char type[10];

	strncpy( type, iHeader->type, 4 );
	type[5] = '\0';
	
	if(type[0] == 'R' && type[1] == 'E' && type[2] == 'A' && type[3] == 'L')
	{
		for(int i = 0; i < iHeader->count; i++)
		{
			fread(image_data[i], FLOAT_SIZE, iHeader->pixels, stack_img);
		}
	}
	else
	{
		cout<<"attempting to read non-REAL file.";
		cout<<"Sorry, I can't do that :-/"<<endl;
		cout<<"file type = "<<type<<endl;
		exit(12);
	}

	cout<<"read "<<iHeader->count<<" images from "<<filename<<" with "<<iHeader->pixels<<" dimensions each"<<endl;
	
	// CREATE FIRST NODES
	
	
	vector< Node *> nodeVec;
	
	float firstNode[iHeader->pixels];
	float secondNode[iHeader->pixels];
	
	
	for(int i = 0; i < iHeader->pixels; i++)
	{
		firstNode[i] = 0;
		secondNode[i] = 0;
	}//initalize the locations of first 2 nodes to 0
	
	float average[iHeader->pixels];
	
	for(int i = 0; i < iHeader->count; i++)
	{
		for(int j = 0; j < iHeader->pixels; j++)
		{
			firstNode[j] += image_data[i][j];
		}
	}//calculate average of particles - store in firstNode
	
	for(int i = 0; i < iHeader->pixels; i++)
	{
		firstNode[i] /= iHeader->count;
	}//normalize sum to get average
	
	for(int i = 0; i < iHeader->pixels; i++)
	{
		secondNode[i] = firstNode[i];
	}//initalize the location of secondNode to average (calced above)
	
	
	//************ADDING NOISE TO IMAGES IN A UNREALISTIC WAY 
	//************MAKES ONE OF THE NODES STAY DISTANT
	//************NOT NECESSARY TO DO THIS...
	//addNoise( firstNode, iHeader->pixels );   // add random noise
	//addNoise( secondNode, iHeader->pixels );  // add random noise
	
	
	nodeVec.push_back( new Node( firstNode, 0 ) );
	nodeVec.push_back( new Node( secondNode, 0 ) );
	
	
	nodeVec[0]->makeEdge( nodeVec[1] );
	

	//LOOP THROUGH ALGORITHM
	
	int currentImageIndex = 0;
	float closestDist = 1000000000;
	float sec_closestDist = 1000000000;
	
	int closestInd = -1;
	int sec_closestInd = -1;
	float tempDist = 0;

	char distFilename[256];
	strcpy( distFilename, outfile );
	strcat( distFilename, ".error" );

	ofstream distFile( distFilename );

	char matchFilename[256];
	strcpy( matchFilename, outfile );

	char tempFilename[256];
	int temp1, temp2;

	vector<float> matches;

	for(int i = 0; i < numPres; i++)
	{

		currentImageIndex = rand() % iHeader->count;
		closestDist = 1000000000;
		sec_closestDist = 1000000000;

		if( i % 1000 == 0 )
		{
			cout<<"presenting network with image "<<i<<" of "<<numPres<<endl;
			cout<<"learning values are : "<<Node::primLearn<<" and "<<Node::secLearn<<endl;
			cout<<"nodes present = "<<nodeVec.size()<<endl;

			float totEdge = 0;
			float totAge = 0;

			for( int countEdge = 0; countEdge < nodeVec.size(); countEdge++)
			{
				totEdge += (float)nodeVec[countEdge]->getNumEdges( );
				totAge += (float)nodeVec[countEdge]->getTotEdgeAge( );
			}
			totAge /= totEdge;  //divide total edge age by number of edges to get average
			totEdge /= (float)nodeVec.size();  //divide number of edges by number of nodes to get average
			

			cout<<"average connectivity = "<<totEdge<<endl;
			cout<<"average edge age = "<<totAge<<endl<<endl;

			/*strcpy( tempFilename, matchFilename );
			
			strcat( tempFilename, "_match." );
			strcat( tempFilename, fcvt( (float)(i), 0, &temp1, &temp2 ) );

			ofstream matchFilename( tempFilename );

			for( int match = 0; match < nodeVec.size(); match++ )
			{
				matches.push_back( nodeVec[match]->checkDist( image_data[currentImageIndex] ) );
			}

			sort( matches.begin(), matches.end() ); //sort vector for output
			for( int outMatch = 0; outMatch < matches.size(); outMatch ++ )
			{
				matchFilename<<outMatch+1<<"\t"<<matches[outMatch]<<endl;
			}

			matchFilename.close();
			matches.clear();*/ // THIS BLOCK OUTPUTS MATCH DISTRIBUTION FOR THIS ROUND

		}
		
		
		closestInd = -1;
		sec_closestInd = -1;
		
		for(int j = 0; j < nodeVec.size(); j++)
		{
		   tempDist = nodeVec[j]->checkDist( image_data[currentImageIndex] );
		    
		   if( tempDist < closestDist )
		   {
		    	sec_closestDist = closestDist;  //replace second place with first
			sec_closestInd = closestInd;
		    
		    	closestDist = tempDist;		//replace first with new winner
			closestInd = j;
		   }
		   else if( tempDist < sec_closestDist )
		   {
		    	sec_closestDist = tempDist;	//else just replace second place if
			sec_closestInd = j;		//qualified
		   }
		     
		}

		distFile<<i<<"\t"<<closestDist<<endl;
		 
		//now we have the best 2 nodes -> adjust closest and create connection if none exists
		 
		nodeVec[closestInd]->moveToward( image_data[currentImageIndex] );  //learning takes place here!
		nodeVec[closestInd]->addError( closestDist );
						 
		nodeVec[closestInd]->makeEdge( nodeVec[sec_closestInd] );  //connect first and second
		 
		//decrease learning rates as data is presented.  Allows for convergence
		Node::secLearn = en*(numPres - (i/LAMBDA_DECAY))/numPres;
		Node::primLearn = eb*(numPres - (i/LAMBDA_DECAY))/numPres;

		for( int eDec = 0; eDec < nodeVec.size(); eDec++ )
		{
			nodeVec[eDec]->decreaseError( D_ERROR_FACTOR ); //decrease everyone's error
		}

		//add another node if it's time
		if( nodeVec.size() < maxNodes && i % addInterval == 0 && i > 0)
		{
			float topError = 0;
			int topInd = -1;

			for( int loop = 0; loop < nodeVec.size(); loop++ )
			{
				if( nodeVec[loop]->getError() > topError )
				{
					topError = nodeVec[loop]->getError();
					topInd = loop;
				}
			}

			if( nodeVec[topInd]->getNumEdges() == 0 )
			{
				closestDist = 1000000000;
				closestInd = -1;
				for( int loop = 0; loop < nodeVec.size(); loop++ )
				{
					if( topInd != loop  )
					{
						tempDist = nodeVec[loop]->checkDist( nodeVec[topInd]->getLoc() );
						if( tempDist < closestDist )
						{
							closestDist = tempDist;
							closestInd = loop;
						}
					}//find closest node to node with highest error to create an edge, since none exists
				}

				nodeVec[topInd]->makeEdge( nodeVec[closestInd] );
				cout<<"creating edge for node addition..."<<endl;

			}			

			nodeVec.push_back( nodeVec[topInd]->makeNode() );

		}
	}

	distFile.close();
	
	//CALC CC VALUE FOR EACH IMAGE AND MAKE CLASS AVERAGES BASED ON WHICH ONE IT BEST MATCHES
	/*float **classAvgs = new float * [nodeVec.size()];
	int *classNum = new int [nodeVec.size()];

	for(int i = 0; i < nodeVec.size(); i++)
	{
		classAvgs[i] = new float[iHeader->pixels];
		classNum[i] = 0;
	}//make image space for new class averages
	
	float bestCC = -99999999;
	int bestInd = 0;
	float temp = 0;

	for(int i = 0; i < iHeader->count; i++ ) //for each particle
	{
		for( int j = 0; j < nodeVec.size(); j++ ) //check match to each unit image
		{
			temp = calcCC( image_data[i], nodeVec[j]->getLoc(), iHeader->pixels );
			
			if( temp > bestCC )
			{
				bestCC = temp;
				bestInd = j;
			}
		}
	
		for( int z = 0; z < iHeader->pixels; z++ )
		{
			
		}

	}*/// Not implemented yet!!!!!!!!!!!!!!!!********************


	//CALCULATE THE CLOSEST NODE FOR EACH IMAGE AND ADD THAT IMAGE TO THAT NODE'S "AVERAGE"

	
	
	for(int i = 0; i < iHeader->count; i ++)
	{	
		if( i % 1000 == 0 )
		{
			cout<<"calculating class average : "<<i<<endl;
		}

		closestDist = 1000000000;
		closestInd = -1;
		for(int j = 0; j < nodeVec.size(); j++)
		{
			tempDist = nodeVec[j]->checkDist( image_data[i] );
	    
			if( tempDist < closestDist )
			{    
				closestDist = tempDist;		//replace first with new winner	
				closestInd = j;
			}	     
		}

		if( closestInd >= 0 )
			nodeVec[closestInd]->addToAvg( image_data[i], i + 1 ); 
								// add one to get correct index into image file
		else
			cout<<"unable to find closest node for image : "<<i<<endl;
	}

	for(int j = 0; j < nodeVec.size(); j++)
	{
		nodeVec[j]->calcAvg();
	}

	char buffer[256];
	

	//OUTPUT CLASS MEMBERSHIPS
	for( int i = 0; i < nodeVec.size(); i++ )
	{
		char outfile_list[256];
		strcpy( outfile_list, outfile );
		strcat( outfile_list, "_class_");
		if( i < 9 )
		{
			strcat( outfile_list, "000" );
			sprintf( buffer, "%d", i+1 );
			strcat( outfile_list, buffer );
		}
		else if( i < 99 )
		{
			strcat( outfile_list, "00" );
			sprintf( buffer, "%d", i+1 );
			strcat( outfile_list, buffer );
		}
		else if( i < 999 )
		{
			strcat( outfile_list, "0" );
			sprintf( buffer, "%d", i+1 );
			strcat( outfile_list, buffer );
		}
		else
		{
			sprintf( buffer, "%d", i+1 );
			strcat( outfile_list, buffer );
		}

		strcat( outfile_list, ".spi" );
		ofstream classList( outfile_list );

		vector< int > * parts = nodeVec[i]->getParts();

		classList<<" ;spi/spi"<<endl;
		for( int j = 0; j < parts->size(); j++ )
		{
			classList<<"\t"<<j+1<<"\t1\t"<<(*parts)[j]<<endl;
		}
	}

	////////////////////////////////////////////////////////////////////////////////////////

	//OUTPUT NODE IMAGES

	//modifying iHeader (original input header) to be output for all images sequentially
	
	char outfile_hed[256];
	char outfile_img[256];
	
	strcpy( outfile_hed, outfile );
	strcpy( outfile_img, outfile );
	strcat( outfile_hed, ".hed" );
	strcat( outfile_img, ".img" );
	
	FILE *out_hed, *out_img;
			
	out_hed = fopen( outfile_hed, "wb" );
	out_img = fopen( outfile_img, "wb" );
	
	float * temp;
	
	cout<<"total number of node images = "<<nodeVec.size()<<endl;
	
	for(int i = 0; i < nodeVec.size(); i++)
	{
		iHeader->imnum = i+1;
		iHeader->count = nodeVec.size()-1;
		
		fwrite( iHeader, 4, 256, out_hed );
	
		temp = nodeVec[i]->getLoc( );
		
		fwrite( temp, FLOAT_SIZE, iHeader->pixels, out_img );
		    
	}


	//////////////////////////////////////////////////////////////////


	//OUTPUT AVERAGE IMAGES

	char outfile_avg_hed[256];
	char outfile_avg_img[256];
	
	strcpy( outfile_avg_hed, outfile );
	strcpy( outfile_avg_img, outfile );
	strcat( outfile_avg_hed, "_avg.hed" );
	strcat( outfile_avg_img, "_avg.img" );

	cout<<"outputing average images to : "<<outfile_avg_hed<<endl;
	
	FILE *out_avg_hed, *out_avg_img;
			
	out_avg_hed = fopen( outfile_avg_hed, "wb" );
	out_avg_img = fopen( outfile_avg_img, "wb" );
	
	cout<<"total number of avg images = "<<nodeVec.size()<<endl;
	
	for(int i = 0; i < nodeVec.size(); i++)
	{
		iHeader->imnum = i+1;
		iHeader->count = nodeVec.size()-1;
		
		fwrite( iHeader, 4, 256, out_avg_hed );
	
		temp = nodeVec[i]->getAvgLoc( );
		
		fwrite( temp, FLOAT_SIZE, iHeader->pixels, out_avg_img );
		    
	}



	///////////////////////////////////////////////////////////////////


	//  CREATE 2D MAP OF NETWORK AND OUTPUT

	//*******************************************

/*	Node *** SAGrid = new Node ** [GRID_SIZE];

	for(int i = 0; i < GRID_SIZE; i++ )
	{
		SAGrid[i] = new Node * [GRID_SIZE];

		for( int j = 0; j < GRID_SIZE; j ++ )
		{
			SAGrid[i][j] = NULL;
		}
	} // setup grid system for map
	
	int tempX = 0;
	int tempY = 0;

	for( int i = 0; i < nodeVec.size(); i++ )
	{
		while( 1 )
		{
			tempX = rand() % GRID_SIZE;
			tempY = rand() % GRID_SIZE;
		
			if( SAGrid[tempX][tempY] == NULL )
			{
				SAGrid[tempX][tempY] = nodeVec[i];
				nodeVec[i]->setGridLoc( tempX, tempY );
				break;
			}
		}
	} // initialize grid with nodes randomly

	int ind = 0;
	int deltaX = 0;
	int deltaY = 0;
	int X = 0;
	int Y = 0;
	int oldX = 0;
	int oldY = 0;
	float T = INIT_TEMP;
	float p = 0;
	float prob = 0;

	float energy = 0;
	float newEnergy = 0;
	float deltaEnergy = 0;

	energy = calcEnergy( SAGrid, &nodeVec );

	///*
	for( int i = 0; i < ANNEAL_ITER; i++ )
	{	
		T = (float)INIT_TEMP * exp( -1 * (float)i / (float)TIME_CONSTANT );

		if( i % 1000 == 0 )
		{
			cout<<"Doing Annealing iteration "<<i<<" of "<<ANNEAL_ITER<<endl;
			cout<<"Temp Value is : "<<T<<" and energy is : "<<energy<<endl;
		}

		ind = rand() % nodeVec.size();
		
		deltaX = (rand() % DELTA_RANGE) - (DELTA_RANGE/2);
		deltaY = (rand() % DELTA_RANGE) - (DELTA_RANGE/2);

		oldX = nodeVec[ind]->getGridX();
		oldY = nodeVec[ind]->getGridY();

		X = oldX + deltaX;
		Y = oldY + deltaY;

		if( X < 0 || X >= GRID_SIZE || Y < 0 || Y >= GRID_SIZE )
		{
			continue;
		}// check boundaries on the grid

		if( SAGrid[X][Y] != NULL )
		{
			continue;
		}  //try again if you're tying to move into an occupied space

		SAGrid[oldX][oldY] = NULL;  //vacate old place
		SAGrid[X][Y] = nodeVec[ind];  //move to new place

		nodeVec[ind]->setGridLoc( X, Y );

		newEnergy = calcEnergy( SAGrid, &nodeVec );
		

		if( newEnergy < energy )
		{
			energy = newEnergy;
			continue;
		}// if new energy is less than last iteration -> accept unconditionally

		deltaEnergy = energy - newEnergy;

		prob = exp( deltaEnergy / T );

		p = (float)(rand( ) % 10000) / 10000.0000;

		if( p < prob )
		{
			energy = newEnergy;
			continue;
		}//if new energy is higher, but allowed based on temp, then keep it
		
		//else it's rejected
		SAGrid[ X ][ Y ] = NULL;
		SAGrid[ oldX ][ oldY ] = nodeVec[ind];
		nodeVec[ind]->setGridLoc( oldX, oldY );
		

	}// grid is set up with final positions

	//*/  //COMMENT OUT TO CHECK RANDOMNESS OF STARTING PLACES

	//for now just output the entire grid.  THIS IS A BIG FILE!!!!!!!!!!!!1

/*	int picDim = (int)sqrt( (float)iHeader->pixels );
	cout<<"outputing map : assuming "<<picDim<<" by "<<picDim<<" images"<<endl;

	int mapX = GRID_SIZE*picDim;
	int mapY = GRID_SIZE*picDim;
	int mapSize = (GRID_SIZE*picDim)*(GRID_SIZE*picDim);
	int mapIndex = 0;
	float * nodeInfo;

	float *mapOutput = new float[mapSize];

	for( int i = 0; i < mapSize; i++ )
	{
		mapOutput[i] = 0;
	}

	for( int i = 0; i < nodeVec.size(); i++ )
	{
		nodeInfo = nodeVec[i]->getLoc();
		for( int j = 0; j < iHeader->pixels; j++ )
		{
			//cout<<"in printing loop.  j = "<<j<<endl;
			mapIndex = nodeVec[i]->getGridY() * picDim * mapY;  //0 y for image
			mapIndex += (j / picDim) * mapY; // raster forward for each row
			mapIndex += (j % picDim);	//raster forward for x
			mapIndex += nodeVec[i]->getGridX() * picDim;
			mapOutput[mapIndex] = nodeInfo[j];
		}
	}// fill in map in correct places

	//OUTPUT MAP TO FILE
	char outfile_map_hed[256];
	char outfile_map_img[256];

	strcpy( outfile_map_hed, outfile );
	strcpy( outfile_map_img, outfile );
	strcat( outfile_map_hed, "_map.hed" );
	strcat( outfile_map_img, "_map.img" );
	
	FILE *out_map_hed, *out_map_img;
			
	out_map_hed = fopen( outfile_map_hed, "wb" );
	out_map_img = fopen( outfile_map_img, "wb" );

	cout<<"opened map image files for writing..."<<endl;

	iHeader->pixels = mapSize;
	iHeader->imnum = 1;
	iHeader->count = 0;
	iHeader->nx = mapX;
	iHeader->ny = mapY;
	
	cout<<"writing map image..."<<endl;
		
	fwrite( iHeader, 4, 256, out_map_hed );
	
	fwrite( mapOutput, FLOAT_SIZE, iHeader->pixels, out_map_img );
*/
	/////////////////////////////////////////////////////
	
	//CLEAN UP MEMORY!!!!!!!!!1

	for( int i = 0; i < nodeVec.size(); i++)
	{
		nodeVec[i]->deleteEdges( );
	}

	for( int i = 0; i < nodeVec.size(); i++)
	{
		delete nodeVec[i];
	}

	



	//EXIT

	return 0;
	
	
}


void addNoise( float *location, int numDim )	//adds uniform noise  +- 0.5 to each pixel
{
    for(int i = 0; i < numDim; i++)
    {
    	location[i] += ((float)(rand() % 1000)/1000.0) - 0.5;
    }
    
	      
}

float getGaussianRand( float sigma )
{
	return -1;
}// not implimented yet!!!!!!!!11


float calcEnergy( Node ***SAGrid, vector<Node *> * nodeVec )
{
	float energy = 0;
	float eNode = 0;
	float eUnit = 0;
	float dX = 0;
	float dY = 0;

	for( int i = 0; i < nodeVec->size() - 1; i++ )
	{
		eNode += (*nodeVec)[i]->getGridDistFromNeighbors( );
	} // loop over edge connections with 2x duplication

	eNode /= 2 * SA_EDGE_WEIGHT; // normalize eNode due to double counting
	
	for( int i = 0; i < nodeVec->size() - 1; i++ )
	{
		for( int j = i; j < nodeVec->size(); j++ )
		{
			if(  !(*nodeVec)[i]->isConnectedTo( (*nodeVec)[j] ) )
			{
				dX = (*nodeVec)[i]->getGridX( ) - (*nodeVec)[j]->getGridX( );
				dY = (*nodeVec)[i]->getGridY( ) - (*nodeVec)[j]->getGridY( );

				eUnit += (dX * dX) + (dY + dY);
			}// only assess closeness penalty if nodes aren't connected
		}
	}

	eUnit *= eUnit * eUnit; // square unit energy as per equation in paper
	//cubing works better...


	float endeUnit = ((float)SA_UNIT_WEIGHT * (float)SA_UNIT_WEIGHT * (float)nodeVec->size() * (float)nodeVec->size() / eUnit);


	if( rand() % 1000 == 1 )
	{
		cout<<"eNode = "<<eNode<<endl;
		cout<<"eUnit = "<<endeUnit<<endl;
	}

	energy = eNode + endeUnit;

	return energy;
}//comment out eUnit to prevent odd clustering





