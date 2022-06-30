#!/usr/bin/env python
#

"""
1. Write equivalent python code -- done 
2. convert python code to use .mrc images -- done 
3. integrate with prtclAlignment.py 
"""

# from concurrent.futures import process
import os
from random import randint
import sys

# import apDisplay
import apRelion
from appionlib.apImage import imagenorm, imagefilter
from pyami import mrc, imagefun
from apImagicFile import readImagic

import numpy as numpy

from tqdm import tqdm
from joblib import Parallel, delayed
import psutil
import multiprocessing as mp

import gc 

N = mp.cpu_count()


FLOAT_SIZE = 4
D_ERROR_FACTOR = 0.995  # decrease error of all Node by this factor each iteration
LAMBDA_DECAY = (
    1
)  # factor to slow decrease of learning rate (1 is no change) higher -> slower
GRID_SIZE = 50
ANNEAL_ITER = 200000
TIME_CONSTANT = 20000
DELTA_RANGE = 41
INIT_TEMP = 20000
SA_UNIT_WEIGHT = 5000000
SA_EDGE_WEIGHT = 1000
ADD_SPEED_FACTOR = (
    1
)  # this changes the way the nodes are added.  When 2, all nodes are added by the
# midpoint of the run


def create_circular_mask(h, w, center=None, radius=None, soft_mask=True):
    if center is None:  # use the middle of the image
        center = (int(w / 2), int(h / 2))
    if radius is None:  # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w - center[0], h - center[1]) * 0.8
    Y, X = numpy.ogrid[:h, :w]
    dist_from_center = numpy.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
    mask = 1 * (dist_from_center <= radius)
    if soft_mask:
        mask = mask.astype("float64")
        sigma = radius / 4
        for i in range(len(mask)):
            for j in range(len(mask[0])):
                if mask[i, j] == 0:
                    r = ((i - w / 2) ** 2 + (j - h / 2) ** 2) ** 0.5
                    mask[i, j] = numpy.exp(-0.5 * ((r - radius) / sigma) ** 2)
    return mask


def mask_stack(stack, radius=None, soft_mask=True):
    mask = create_circular_mask(stack.shape[-2], stack.shape[-1], radius, soft_mask)
    return mask * stack


def array_from_star(starfile):
    print("Getting particle files from .star file...")
    img_list = apRelion.getMrcParticleFilesFromStar(starfile)
    numparts_dict = {}
    N = 0
    for pimg in tqdm(img_list):
        with open(starfile) as file:
            s = 0
            i = 0
            for line in file:
                img = pimg.split("micrographs/")[1]
                if img in line:
                    s += 1
            numparts_dict[pimg] = s
            N += s
    cd = os.getcwd()
    star_dir = os.path.dirname(os.path.abspath(starfile))
    os.chdir(star_dir)
    print("Generating particle array from particle mrc files...")
    particle_array = numpy.concatenate(
        Parallel(n_jobs=-1)(delayed(mrc.read)(pimg) for pimg in tqdm(img_list)), axis=0
    )
    gc.collect()
    os.chdir(cd)
    if len(particle_array) != N:
        error_msg = f"{N} particles were listed in {starfile}, but only {len(particle_array)} were read from the listed images"
        raise Exception(error_msg)
    return particle_array


def process_particle(particle, params=None):
    ### step 1 filter particle
    if params["lowpass"]:
        particle = imagefilter.lowPassFilter(
            particle, apix=params["apix"], radius=params["lowpass"]
        )
    if params["highpass"]:
        particle = imagefilter.tanhHighPassFilter(
            particle, params["highpass"], apix=params["apix"]
        )
    ### step 2 unless specified, invert the images # moved to process_stack()
    # if params["invert"] is True:
    #     particle = -1.0 * particle
    ### step 3 normalize particle
    # normoptions = ('none', 'boxnorm', 'edgenorm', 'rampnorm', 'parabolic') #normalization
    if params["normalization"] in [True, "boxnorm"]:
        particle = imagenorm.normStdev(particle)
    elif params["normalization"] == "edgenorm":
        particle = imagenorm.edgeNorm(particle)
    elif params["normalization"] == "rampnorm":
        particle = imagenorm.rampNorm(particle)
    elif params["normalization"] == "parabolic":
        particle = imagenorm.parabolicNorm(particle)
    # if params["normalization"] is not None:
    #     particle = (particle - particle.mean())/particle.std()
    ### step 4: decimate/bin particles if specified
    ### binning is last, so we maintain most detail and do not have to deal with binned apix
    if params["bin"] > 1:
        particle = imagefun.bin2(particle, params["bin"])
    return particle


def process_stack(stack, params):
    # return stack 
    stack = numpy.stack(
        Parallel(n_jobs=-1)(
            delayed(process_particle)(part, params) for part in tqdm(stack)
        ),
        axis=0,
    )
    gc.collect()

    # with mp.Pool(processes=N) as pool:
    #     stack = pool.map(process_particle, [(stack[i], params) for i in range(len(stack))])
    #     stack = numpy.stack(stack)
    # if params["premask"]:
    #     stack = mask_stack(stack)
    # if params["invert"]:
    #     stack *= -1 
    # gc.collect()

    # stack = numpy.stack([process_particle(stack[i], params) for i in tqdm(range(len(stack)))])

    if 'partfile' in params.keys():
        print("Writing preprocessed particle stack to disk...")
        mrc.write(stack, params['partfile'])
        gc.collect()

    return stack


class Node:
    def __init__(self, location, error):
        self.myLocation = location.copy()
        self.myAvgLocation = numpy.zeros_like(location)
        self.myError = error
        self.myAvgImNum = 0
        self.edges = []
        self.particles = []

    def _Node(self):
        del self.myLocation
        del self.myAvgLocation
        self.edges = []
        self.particles = []

    def checkDist(self, location):
        return numpy.power(location - self.myLocation, 2).sum()

    def moveToward(self, loc):
        self.myLocation += self.primLearn * (loc - self.myLocation)
        for i in range(len(self.edges)):
            self.edges[i].addImage(self, loc)
            self.edges[i].incAge()
        i = 0
        while i < len(self.edges):
            if self.edges[i].isTooOld():
                self.edges[i].eraseEdge(self)
                del self.edges[i]
                i = -1
            i += 1

    def addImage(self, loc):
        self.myLocation += self.secLearn * (loc - self.myLocation)

    def getLoc(self):
        return self.myLocation

    def getAvgLoc(self):
        return self.myAvgLocation

    def addToAvg(self, img, index):
        self.myAvgLocation += img
        self.myAvgImNum += 1
        self.particles.append(index)

    def calcAvg(self):
        if self.myAvgImNum == 0:
            return
        self.myAvgLocation /= self.myAvgImNum

    def getParts(self):
        return self.particles

    def addError(self, e):
        self.myError += e

    def getError(self):
        return self.myError

    def decreaseError(self, fac):
        self.myError *= fac

    def makeEdge(self, n):
        for i in range(len(self.edges)):
            if self.edges[i].exists(n):
                self.edges[i].resetAge()
                return
        e = Edge(self, n)
        self.edges.append(e)
        n.receiveEdge(e)

    def receiveEdge(self, e):
        self.edges.append(e)

    def eraseEdge(self, e):
        erased = False
        for i in range(len(self.edges)):
            if self.edges[i] == e:
                del self.edges[i]
                erased = True
                break
        if not erased:
            print("Edge to be erased was not found!")

    def isConnectedTo(self, n):
        isConnect = False
        for i in range(len(self.edges)):
            if self.edges[i].isConnectedTo(self, n):
                isConnect = True
                break
        return isConnect

    def getNumEdges(self):
        return len(self.edges)

    def getTotEdgeAge(self):
        totAge = 0
        for i in range(len(self.edges)):
            totAge += self.edges[i].getAge()
        return totAge

    def setEdgeNULL(self, e):
        for i in range(len(self.edges)):
            if self.edges[i] == e:
                self.edges[i] = None

    def deleteEdges(self):
        for i in range(len(self.edges)):
            if self.edges[i] is None:
                continue
            self.edges[i].tellNeighborNULL(self)
            # del self.edges[i]
            self.edges[i] = None

    def makeNode(self):
        topError = -1000
        topInd = -1
        for i in range(len(self.edges)):
            err = self.edges[i].getError(self)
            if topError < err:
                topError = err
                topInd = i
        if (topInd == -1) or (len(self.edges) == 0):
            print("Error finding place for new node... recalculating...")
            return None
        neighborLoc = self.edges[topInd].getLoc(self)
        newLoc = 0.5 * (neighborLoc + self.myLocation)
        self.myError *= self.alpha
        self.edges[topInd].decreaseError(self, self.alpha)
        newNode = Node(newLoc, self.myError)
        self.edges[topInd].makeConnection(self, newNode)
        self.makeEdge(newNode)
        self.edges[topInd].eraseEdge(self)
        del self.edges[topInd]
        # self.edges.erase(self.edges.begin() + topInd)
        return newNode

    # GRID FUNCTIONS
    def setGridLoc(self, x, y):
        self.gridX = x
        self.gridY = y

    def getGridX(self):
        return self.gridX

    def getGridY(self):
        return self.gridY

    def getGridDistFromNeighbors(self):
        for i in range(len(self.edges)):
            tempX = self.edges[i].getGridX(self)
            tempY = self.edges[i].getGridY(self)
            dX = self.gridX - tempX
            dY = self.gridY - tempY
            totalDist += dX ** 2 + dY ** 2
        return totalDist

    # # # # # # # # 

    def setDim(self, d):
        self.dim = d

    def getDim(self):
        return self.dim


class Edge:
    def __init__(self, f: Node, s: Node):  # , maxAge: int) -> None:
        self.Edge(f, s)  # , maxAge)

    def Edge(self, f: Node, s: Node):  # , maxAge: int) -> None:
        self.first = f
        self.second = s
        self.age = 1
        # self.maxAge = maxAge

    def figurePolarity(self, n: Node) -> Node:
        if n == self.first:
            return self.second
        if n == self.second:
            return self.first
        print("Error assigning directinoality at edge!")
        return None

    def addImage(self, t: Node, im: float) -> None:
        self.figurePolarity(t).addImage(im)

    def incAge(self) -> None:
        self.age += 1

    def resetAge(self) -> None:
        self.age = 1

    def getAge(self) -> int:
        return self.age

    def isTooOld(self) -> bool:
        return self.age >= self.maxAge

    def exists(self, n: Node) -> bool:
        if (self.first == n) or (self.second == n):
            return True
        return False

    def getError(self, n: Node) -> float:
        return self.figurePolarity(n).getError()

    def getLoc(self, n: Node) -> float:
        return self.figurePolarity(n).getLoc()

    def decreaseError(self, n: Node, f: float) -> None:
        self.figurePolarity(n).decreaseError(f)

    def makeConnection(self, n: Node, newNode: Node) -> None:
        self.figurePolarity(n).makeEdge(newNode)

    def eraseEdge(self, n: Node) -> None:
        self.figurePolarity(n).eraseEdge(self)

    def getGridX(self, n: Node) -> int:
        return self.figurePolarity(n).getGridX()

    def getGridY(self, n: Node) -> int:
        return self.figurePolarity(n).getGridY()

    def isConnectedTo(self, n: Node, neighbor: Node) -> bool:
        isConnected = False
        if self.figurePolarity(n) == neighbor:
            isConnected = True
        return isConnected

    def tellNeighborNULL(self, n: Node) -> None:
        self.figurePolarity(n).setEdgeNull(self)


class Header:
    def __init__(self):
        pass



def CAN(input_stack, output_stack, can_params, process_params=None, return_parts=False):
    if False:  # NEEDS TO BE UPDATED
        print("usage : ", " <input stack> <output stack> <# of iterations> ")
        print(
            "<direct learning rate> <indirect learning rate> <max age> <total # of nodes in network>\n "
        )
        print(
            "<input stack> : input numpy stack OR .mrcs stack path (usually output of an MRA)"
        )
        print(
            "<output stack> : output .mrcs file name for the classification images (unit images not averages!)"
        )
        print(
            "<# of iterations> : number of times data will be presented to the network.  This number"
        )
        print(
            "should be ~15 or more times greater than your number of particles in <input imagic stack>"
        )
        print(
            "<direct learning rate> : fraction that closest unit image will be moved toward presented data (paper suggests .01 for cryoEM, higher for neg stain?  EXPERIMENT!)"
        )
        print(
            "<indirect learning rate> : fraction that connection unit images will be moved (same advice as above! except .0005 is recommended - should be lower than direct rate)"
        )
        print(
            "<max age> : number of iterations an edge connecting two units can be unused before it's discarded (paper suggests 30-40, experiment with this too!  I've found ~20 gives better sampling of all views)"
        )
        print(
            "<total # of nodes in network> : should be on the order of 20 times less than particle number"
        )
        print(
            "*********Implimentation of 'Topology representing network enables highly accurate classification of protein images taken by cryo electron-microscope without masking' by Ogura, Iwasaki and Sato (2003) J. Struct. Bio."
        )
        return

    # extract parameters
    stack, outfile, numPres, eb, en, maxAge, maxNodes = (
        input_stack,
        output_stack,
        can_params["numpres"],
        can_params["learn"],
        can_params["ilearn"],
        can_params["maxage"],
        can_params["numClasses"],
    )
    if ".mrc" not in outfile[-4:]:
        outfile += ".mrcs"
    numPres = int(numPres)
    eb = float(eb)
    en = float(en)
    maxAge = int(maxAge)
    maxNodes = int(maxNodes)
    print(f"maxNodes = {maxNodes}\n")
    addInterval = int(
        numPres / maxNodes / ADD_SPEED_FACTOR
    )  # number of iterations between adding new nodes

    if type(stack) not in [numpy.array, numpy.ndarray, str]:
        # print(type(stack))
        # print(stack)
        raise Exception(
            "Ensure that input stacks are of the type np.array or a string path to the mrc stack file."
        )

    # set node variables
    Node.secLearn = en
    Node.primLearn = eb
    Node.alpha = 0.5
    Edge.maxAge = maxAge

    # organize image data
    if type(stack) == numpy.ndarray:
        image_data = stack.copy()
        del stack
    else:
        print("Reading stack data...")
        try:
            if stack.endswith(".star"):
                image_data = array_from_star(stack)
            elif stack.endswith(".hed") or stack.endswith(".img"):
                image_data = readImagic(stack)["images"]
            else:
                image_data = mrc.read(stack)
        except:
            raise Exception(
                "Input stack should be a numpy array, .star stack path, or an .mrc/.mrcs stack path."
            )
    if process_params is not None:
        image_data = process_stack(image_data, process_params)

    dims = image_data.shape
    stack_hed = dict(
        zip(
            ["nimg", "rows", "lines", "npix"],
            [dims[0], dims[1], dims[2], dims[1] * dims[2]],
        )
    )

    print("DIAGNOSTIC FILE INFO")
    for key in stack_hed.keys():
        print(f"{key} = {stack_hed[key]}")
    print("\n ")
    # define object in accordance with C program's use, for development convenience
    iHeader = Header()
    iHeader.pixels = stack_hed["npix"]
    iHeader.count = stack_hed["nimg"]
    iHeader.nx = stack_hed["rows"]
    iHeader.ny = stack_hed["lines"]
    Node.d = iHeader.pixels

    # print(
    #     f"Read {iHeader.count} images from {filename} with {iHeader.pixels} dimensions each"
    # )

    # Create first nodes
    firstNode = image_data.sum(axis=0) / len(image_data)
    secondNode = firstNode.copy()
    firstNode = Node(firstNode, 0)
    secondNode = Node(secondNode, 0)
    nodeVec = [firstNode, secondNode]
    nodeVec[0].makeEdge(nodeVec[1])

    # Loop through algorithm
    currentImageIndex = 0
    closestDist = 1000000000
    sec_closestDist = 1000000000

    closestInd = -1
    sec_closestInd = -1
    tempDist = 0

    distFilename = outfile.replace("mrcs", "error")
    distFile = open(distFilename, "wb")

    for i in range(numPres):
        currentImageIndex = randint(0, iHeader.count - 1)
        closestDist = 1000000000
        sec_closestDist = 1000000000
        if i % 1000 == 0:
            print(f"Presenting network with image {i} of {numPres}")
            print(f"Learning values are: {Node.primLearn:.2e} and {Node.secLearn:.2e}")
            print(f"Nodes present = {len(nodeVec)}")

            avgEdge = 0
            avgAge = 0

            for countEdge in range(len(nodeVec)):
                avgEdge += nodeVec[countEdge].getNumEdges()
                avgAge += nodeVec[countEdge].getTotEdgeAge()

            avgAge /= avgEdge
            avgEdge /= len(nodeVec)

            print(f"Avgerage connectivity = {avgEdge:.2f}")
            print(f"Average edge age = {avgAge:.2f}\n")

        closestInd = -1
        sec_closestInd = -1
        for j in range(len(nodeVec)): # could parallelize here 
            tempDist = nodeVec[j].checkDist(
                image_data[currentImageIndex]
            )  # nodeVec[j].myLocation is on the order of 10**5

            if tempDist < closestDist:
                sec_closestDist = closestDist
                sec_closestInd = closestInd
                closestDist = tempDist
                closestInd = j
            elif tempDist < sec_closestDist:
                sec_closestDist = tempDist
                sec_closestInd = j
        distFile.write(f"{i}\t{closestDist}\n".encode())
        # now we have the best 2 nodes -> adjust closest and create connection if none exists
        nodeVec[closestInd].moveToward(
            image_data[currentImageIndex]
        )  # learning takes place here!
        nodeVec[closestInd].addError(closestDist)
        nodeVec[closestInd].makeEdge(
            nodeVec[sec_closestInd]
        )  # connect first and second

        # decrease learning rates as data is presented.  Allows for convergence
        Node.secLearn = en * (numPres - (i / LAMBDA_DECAY)) / numPres
        Node.primLearn = eb * (numPres - (i / LAMBDA_DECAY)) / numPres

        for eDec in range(len(nodeVec)):
            nodeVec[eDec].decreaseError(D_ERROR_FACTOR)  # decrease everyone's error

        # add another node if it's time
        if (len(nodeVec) < maxNodes) and (i % addInterval == 0) and (i > 0):
            topError = 0
            topInd = -1
            for loop in range(len(nodeVec)):
                if nodeVec[loop].getError() > topError:
                    topError = nodeVec[loop].getError()
                    topInd = loop

            if nodeVec[topInd].getNumEdges() == 0:
                closestDist = 1000000000
                closestInd = -1
                for loop in range(len(nodeVec)):
                    if topInd != loop:
                        tempDist = nodeVec[loop].checkDist(nodeVec[topInd].getLoc()) # could parallelize 
                        if tempDist < closestDist:
                            closestDist = tempDist
                            closestInd = loop
                nodeVec[topInd].makeEdge(nodeVec[closestInd])
                print("Creating edge for node addition...")

            nodeVec.append(nodeVec[topInd].makeNode())
    distFile.close()

    for i in range(iHeader.count):
        if i % 1000 == 0:
            print(f"Calculating class average {i}")
        closestDist = 1000000000
        closestInd = -1
        for j in range(len(nodeVec)):
            tempDist = nodeVec[j].checkDist(image_data[i])
            if tempDist < closestDist:
                closestDist = tempDist
                closestInd = j
        if closestInd >= 0:
            nodeVec[closestInd].addToAvg(image_data[i], i + 1)
        else:
            print(f"Unable to find closest node for iamge {i}")

    for i in range(len(nodeVec)):
        nodeVec[i].calcAvg()

    for i in range(len(nodeVec)):
        outfile_list = outfile.replace(".mrcs", "") + "_class_"
        if i < 9:
            outfile_list += f"000{i+1}"
        elif i < 99:
            outfile_list += f"00{i+1}"
        elif i < 999:
            outfile_list += f"0{i+1}"
        else:
            outfile_list += f"{i+1}"
        outfile_list += ".spi"

        classList = open(outfile_list, "wb")
        parts = nodeVec[i].getParts()
        for j in range(len(parts)):
            classList.write(f"\t{j+1}\t1\t{parts[j]}".encode())
        classList.close()

    ############################################

    # OUTPUT NODE IMAGES

    # modifying iHeader (original input header) to be output for all images sequentially

    # outstack = image_data[:maxNodes] # generate meaningless stack for testing purposes -- uncomment 491 to 655 when done

    outstack = numpy.stack([nodeVec[i].getAvgLoc() for i in range(len(nodeVec))])
    if outfile is not None:
        mrc.write(outstack, outfile)

    if return_parts is True:
        return {"particles": image_data, "classes": outstack}


if __name__ == "__main__":
    star_path = "/gpfs/group/em/appion/abonham/22may05d/stacks/RS090522/particle.star"
    # cmd = ('start' + " classes 20118 0.010 0.00050 25 10").split(" ")
    # stack = readImagic('start')['images']
    # stack = "start.mrcs"
    # outfile = "classes_avg.mrcs"
    # params = "20118 0.010 0.00050 25 10".split(" ")
    # cmd = [stack, outfile] + params
    outfile = "test"
    can_params = dict(
        zip(["learn", "ilearn", "maxage", "numClasses"], [0.01, 0.0005, 25, 36])
    )
    process_params = dict(
        zip(
            [
                "apix",
                "lowpass",
                "highpass",
                "premask",
                "normalization",
                "bin",
                "invert",
            ],
            [4.47, 10, 2000, False, None, 1, False],
        )
    )

    CAN(star_path, outfile, can_params, process_params)
