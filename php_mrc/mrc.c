#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mrc.h"

static void byteswap2(unsigned char *pbyData) {
	unsigned char byTemp;
	byTemp  = pbyData[0];
	pbyData[0] = pbyData[1];
	pbyData[1] = byTemp;
}

static void byteswap4(unsigned char *pbyData) {
	unsigned char byTemp0;
	unsigned char byTemp1;

	byTemp0  = pbyData[0];
	byTemp1  = pbyData[1];
	pbyData[0] = pbyData[3];
	pbyData[1] = pbyData[2];
	pbyData[2] = byTemp1;
	pbyData[3] = byTemp0;
}

void byteswapbuffer(void *pData, unsigned int uElements, unsigned int uElementSize) {

	unsigned char *pbyData = (unsigned char *)pData;
	unsigned int cuElements = uElements;

	while(cuElements > 0) {
		if(uElementSize == 2)
			byteswap2(pbyData);
		else if(uElementSize == 4)
			byteswap4(pbyData);
		else
			return;
		pbyData += uElementSize;
		cuElements--;
	}
}

int byteswapread(FILE *pFRead, void *pBuffer, unsigned int uElements,
				 unsigned int uElementSize, unsigned int fuByteOrder) {

 	unsigned int uResult = 0;
    uResult = fread((char *)pBuffer, uElementSize, uElements, pFRead);
	if(ferror(pFRead)) {
		return -1;
	}
	
	if(((fuByteOrder == LITTLE_ENDIAN_DATA) && BIG_ENDIAN_HOST) ||
		((fuByteOrder == BIG_ENDIAN_DATA) && LITTLE_ENDIAN_HOST))
		byteswapbuffer(pBuffer, uElements, uElementSize);
    return uResult;
}
// size_t  fwrite ( const void * buffer, size_t size, size_t count, FILE * stream ); 
	// int  fread (void * buffer, size_t size, size_t count, FILE * stream); 


int byteswapwrite(FILE *pFWrite, void *pBuffer, unsigned int uElements,
				 unsigned int uElementSize, unsigned int fuByteOrder) {

 	unsigned int uResult = 0;
	if(((fuByteOrder == LITTLE_ENDIAN_DATA) && BIG_ENDIAN_HOST) ||
		((fuByteOrder == BIG_ENDIAN_DATA) && LITTLE_ENDIAN_HOST))
		byteswapbuffer(pBuffer, uElements, uElementSize);

	uResult = fwrite((char *)pBuffer, uElementSize, uElements, pFWrite);
	if(ferror(pFWrite)) {
		return -1;
	}
	
    return uResult;
}

int readMRCHeader(FILE *pFMRC, MRCHeader *pMRCHeader) {
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;

    byteswapread(pFMRC, &pMRCHeader->nx, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->ny, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nz, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mode, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nxstart, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nystart, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nzstart, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mx, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->my, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mz, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->x_length, 1, 4, fuByteOrder); 
    byteswapread(pFMRC, &pMRCHeader->y_length, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->z_length, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->alpha, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->beta, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->gamma, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mapc, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mapr, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->maps, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->amin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->amax, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->amean, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->ispg, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nsymbt, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->extra, 4*MRC_USER, 1, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->xorigin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->yorigin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->zorigin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->map, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->machstamp, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->rms, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nlabl, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->label, MRC_LABEL_SIZE*MRC_NUM_LABELS, 1, fuByteOrder);
	
    if((pMRCHeader->nx < 0) || (pMRCHeader->ny < 0) || (pMRCHeader->nz < 0) ||
		(pMRCHeader->mode < 0) || (pMRCHeader->mode > 4))
        return -1; /* This is not a valid pMRCHeader header */

	return 1 ;
}

int writeMRCHeader(FILE *pFMRC, MRCHeader *pMRCHeader) {
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;

	byteswapwrite(pFMRC, &pMRCHeader->nx, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->ny, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nz, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mode, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nxstart, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nystart, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nzstart, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mx, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->my, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mz, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->x_length, 1, 4, fuByteOrder); 
	byteswapwrite(pFMRC, &pMRCHeader->y_length, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->z_length, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->alpha, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->beta, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->gamma, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mapc, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mapr, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->maps, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->amin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->amax, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->amean, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->ispg, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nsymbt, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->extra, 4*MRC_USER, 1, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->xorigin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->yorigin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->zorigin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->map, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->machstamp, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->rms, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nlabl, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->label, MRC_LABEL_SIZE*MRC_NUM_LABELS, 1, fuByteOrder);
	
	return 1 ;
}

int writeMRC(FILE *pFMRC, MRC *pMRC) {
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;

	uElements = pMRC->header.nx * pMRC->header.ny; //  * pMRC->header.nz;
	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_FLOAT:
			uElementSize = sizeof(float);
			break;
		case MRC_MODE_SHORT_COMPLEX:
			uElementSize = sizeof(short);
			uElements *= 2;
			break;
		case MRC_MODE_FLOAT_COMPLEX:
			uElementSize = sizeof(float);
			uElements *= 2;
			break;
		default:
			return -1;
	}

	if(!writeMRCHeader(pFMRC, &(pMRC->header)))
		return -1;
	if(byteswapwrite(pFMRC, pMRC->pbyData, uElements, uElementSize, fuByteOrder) == -1)
		return 1;
}





//int loadMRCHeader(char *pszFilename, MRC *pMRC) {
int loadMRCHeader(char *pszFilename, MRCHeader *pMRCHeader) {
	FILE *pFMRC;


	if((pFMRC = fopen(pszFilename, "rb")) == NULL)
		return -1;


	if(!readMRCHeader(pFMRC, pMRCHeader)) {
		fclose(pFMRC);
		return -1;
	}

	fclose(pFMRC);
	return 1;
}



int loadMRC(char *pszFilename, MRC *pMRC) {
	FILE *pFMRC;
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;

	if((pFMRC = fopen(pszFilename, "rb")) == NULL)
		return -1;

	if(!readMRCHeader(pFMRC, &(pMRC->header)))
		return -1;

	uElements = pMRC->header.nx * pMRC->header.ny * pMRC->header.nz;

	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_FLOAT:
			uElementSize = sizeof(float);
			break;
		case MRC_MODE_SHORT_COMPLEX:
			uElementSize = sizeof(short);
			uElements *= 2;
			break;
		case MRC_MODE_FLOAT_COMPLEX:
			uElementSize = sizeof(float);
			uElements *= 2;
			break;
		default:
			return -1;
	}

    if((pMRC->pbyData = malloc(uElements*uElementSize)) == NULL)
    	pMRC->pbyData = malloc(uElements*uElementSize);
	
	if(byteswapread(pFMRC, pMRC->pbyData, uElements, uElementSize, fuByteOrder) == -1) {
		free(pMRC->pbyData);
		fclose(pFMRC);
		return -1;
	}

	fclose(pFMRC);
    return 1;
}

int readImagic5Header(FILE *pFHeader, Imagic5Header *pHeader) {
	unsigned int uResult;
	uResult = fread((void *)pHeader, 1, SIZEOF_I5_HEADER, pFHeader);
	if(ferror(pFHeader) || (uResult != SIZEOF_I5_HEADER))
		return -1;
	return 1;
}

void *readImagic5Images(FILE *pFImage, Imagic5 *pImagic5) {
	void *pData = NULL;
	size_t size = 0;
	unsigned int uResult = 0;
	char *psType = pImagic5->pHeaders[0].type;
	unsigned int uElements = pImagic5->pHeaders[0].npixel;
	
	if(strcmp(psType, "REAL") == 0)
		size = sizeof(float);
	else if(strcmp(psType, "INTG") == 0)
		size = sizeof(short);
	else if(strcmp(psType, "PACK") == 0)
		size = sizeof(char);
	else if(strcmp(psType, "COMP") == 0)
		size = 2*sizeof(float);
	pData = malloc(size * uElements * pImagic5->uCount);
	if(pData == NULL)
		return NULL;

	uResult = fread(pData, 1, size*uElements*pImagic5->uCount, pFImage);
	if(ferror(pFImage)) {
		free(pData);
		return NULL;
	}
/*
	if(!byteswapread(pFImage, pData, size, uElements*pImagic5->uCount, BIG_ENDIAN_DATA)) {
		free(pData);
		return NULL;
	}
*/
	return pData;
}

void freeImagic5(Imagic5 *pImagic5) {

	unsigned int cuImage = 0;

	if(pImagic5->pHeaders != NULL) {
		free(pImagic5->pHeaders);
		pImagic5->pHeaders = NULL;
	}

	if(pImagic5->pbyData != NULL) {
		free(pImagic5->pbyData);
		pImagic5->pbyData = NULL;
	}

	pImagic5->uCount = -1;
}

int readImagic5(FILE *hedstream, FILE *imgstream, Imagic5 *pImagic5) {

	int nResult = -1;
	void *pResult = NULL;
	unsigned int cui = 0;
	Imagic5Header header;

	nResult = readImagic5Header(hedstream, &header);
	if(!nResult)
		return -1;

	pImagic5->uCount = header.ifol + 1;
	if(pImagic5->uCount <= 0)
		return -1;

	pImagic5->pHeaders = (Imagic5Header *)malloc(pImagic5->uCount*SIZEOF_I5_HEADER);
	if(pImagic5->pHeaders == NULL)
		return -1;

	memcpy(&(pImagic5->pHeaders[0]), &header, SIZEOF_I5_HEADER);

	for(cui = 1; cui < pImagic5->uCount; cui++) {
		nResult = readImagic5Header(hedstream, &(pImagic5->pHeaders[cui]));
		if(!nResult) {
			freeImagic5(pImagic5);
			return -1;
		}
	}

	pResult = readImagic5Images(imgstream, pImagic5);
	if(pResult == NULL) {
		freeImagic5(pImagic5);
		return -1;
	}
	
	pImagic5->pbyData = pResult;

	return 1;
}

int loadImagic5(char *pszName, Imagic5 *pImagic5) {
	char *pszFilename = NULL;
	FILE *pFHED = NULL;
	FILE *pFIMG = NULL;

	pszFilename = (char *)malloc(strlen(pszName) + 5);
	if(pszFilename == NULL)
		return -1;

	sprintf(pszFilename, "%s.hed", pszName);
    if((pFHED = fopen(pszFilename, "rb")) == NULL) {
		free(pszFilename);
		return -1;
	}

	sprintf(pszFilename, "%s.img", pszName);
    if((pFIMG = fopen(pszFilename, "rb")) == NULL) {
		free(pszFilename);
		fclose(pFHED);
		return -1;
	}
	free(pszFilename);

	if(!readImagic5(pFHED, pFIMG, pImagic5)) {
		fclose(pFHED);
		fclose(pFIMG);
		return -1;
	}

	fclose(pFHED);
	fclose(pFIMG);
    
    return 1;
}
