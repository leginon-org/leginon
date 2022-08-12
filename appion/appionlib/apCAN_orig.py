#!/usr/bin/env python
#

"""
1. Write equivalent python code -- done 
2. convert python code to use .mrc images -- done 
3. integrate with prtclAlignment.py 
"""
from random import randint

from pyami import mrc

import numpy as numpy

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

    # # # # # # # # /

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


def CAN(args):
    if len(args) != 7:
        print("usage : ", " <input stack> <output stack> <# of iterations> ")
        print(
            "<direct learning rate> <indirect learning rate> <max age> <total # of nodes in network>\n "
        )
        print(
            "<input imagic stack> : input numpy stack OR .mrcs stack path (usually output of an MRA)"
        )
        print(
            "<output imagic stack> : output .mrcs file name for the classification images (unit images not averages!)"
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
    stack, outfile, numPres, eb, en, maxAge, maxNodes = args
    if '.mrc' not in outfile[-4:]:
        outfile += '.mrcs'
    numPres = int(numPres)
    eb = float(eb)
    en = float(en)
    maxAge = int(maxAge)
    maxNodes = int(maxNodes)
    print(f"maxNodes = {maxNodes}\n")
    addInterval = int(
        numPres / maxNodes / ADD_SPEED_FACTOR
    )  # number of iterations between adding new nodes

    if type(stack) not in [numpy.array, str]:
        raise Exception('Ensure that input stacks are of the type np.array or a string path to the mrc stack file.')

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
        try:
            image_data = mrc.read(stack)
        except:
            raise Exception(
                "Input stack should be a numpy array or a path to an mrc stack (ext: .mrcs)."
            )
    dims = image_data.shape
    stack_hed = dict(
        zip(
            ["nimg", "rows", "lines", "npix"],
            [dims[0], dims[1], dims[2], dims[1] * dims[2]],
        )
    )

    print("DIAGNOSTIC FILE INFO")
    for key in stack_hed.keys():
        print(key, "=", stack_hed[key])
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
        for j in range(len(nodeVec)):
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
        distFile.write(f"{i}\t".encode())
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
                        tempDist = nodeVec[loop].checkDist(nodeVec[topInd].getLoc())
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
        outfile_list = outfile.replace('.mrcs', '') + "_class_"
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

    ############################################

    # OUTPUT NODE IMAGES

    # modifying iHeader (original input header) to be output for all images sequentially
    outstack = numpy.stack([nodeVec[i].getAvgLoc() for i in range(len(nodeVec))])
    mrc.write(outstack, outfile)


if __name__ == "__main__":
    # star_path = '/gpfs/group/em/appion/abonham/22may05d/stacks/RS090522/particle.star'
    # cmd = ('start' + " classes 20118 0.010 0.00050 25 10").split(" ")
    # stack = readImagic('start')['images']
    stack = "start.mrcs"
    outfile = "classes_avg.mrcs"
    params = "20118 0.010 0.00050 25 10".split(" ")
    cmd = [stack, outfile] + params
    CAN(cmd)
