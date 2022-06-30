#!/usr/bin/env python
#
import os
import sys
import time
import math
import shutil
import glob
import pickle
import tarfile
import string
import logging
from tqdm import tqdm
from joblib import Parallel, delayed
import psutil
import gc
import numpy
import pandas as pd
from skimage.registration import phase_cross_correlation
from skimage.transform import warp_polar, rotate
from scipy import ndimage
from scipy.ndimage.measurements import center_of_mass

# appion
import sinedon.directq
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack
from appionlib import apParam
from appionlib import appiondata
from appionlib import apProject
from appionlib.apSpider import operations
from appionlib import apCAN
from runStats import profile, get_process_memory
from pyami import mrc


# =====================
# =====================
# Image processing functions


def record_memory(old_mems=None, index=None, write=False):
    if old_mems is None:
        mems = pd.DataFrame(
            [[index] + list(get_process_memory())],
            columns=["phase", "RSS", "VMS", "SHR", "LIB"],
        )
    else:
        mems = old_mems.append(
            dict(
                zip(
                    ["phase", "RSS", "VMS", "SHR", "LIB"],
                    [index] + list(get_process_memory()),
                )
            ),
            ignore_index=True,
        )
    if write:
        mems.to_csv("mems")
    return mems


def align_particle(polar_refs, particle, return_rotation=False):
    errors = [None] * len(polar_refs)
    shifts = errors.copy()
    polar_particle = warp_polar(particle)
    for i in range(len(polar_refs)):
        s, e, p = phase_cross_correlation(
            polar_refs[i], polar_particle, normalization=None
        )
        shifts[i] = s[0]
        errors[i] = e
    ref_match = numpy.argmin(errors)
    aligned = rotate(particle, -shifts[ref_match])
    if return_rotation:
        return aligned, -shifts[ref_match]
    return aligned


@profile
def align_stack(ref_stack, parts, prerotations=None, return_rotations=False):
    # parts_c = center_stack(parts)
    if type(ref_stack) == str:
        ref_stack = mrc.read(ref_stack)
    if type(parts) == str:
        parts = mrc.read(parts)
    if type(prerotations) == str:
        prerotations = pd.read_csv(prerotations, index_col=0)

    polar_refs = numpy.stack([warp_polar(ref_stack[i]) for i in range(len(ref_stack))])

    if prerotations is not None:
        if prerotations.shape[-1] > 0:
            apDisplay.printMsg("Preparing original stack for alignement...")
            parts = Parallel(n_jobs=-1)(
                delayed(rotate)(parts[i], prerotations.iloc[i].sum())
                for i in range(len(parts))
            )
            parts = numpy.stack(parts)
            gc.collect()

    apDisplay.printMsg("Aligning stack to class averages...")
    if return_rotations:
        aligned = Parallel(n_jobs=-1)(
            delayed(align_particle)(polar_refs, parts[i], True)
            for i in tqdm(range(len(parts)))
        )
        gc.collect()
        rotations = numpy.zeros(len(aligned))
        for i in range(len(rotations)):
            aligned[i], rotations[i] = aligned[i]
        aligned = numpy.stack(aligned)
        if prerotations is None:
            prerotations = pd.DataFrame({1: rotations})
        else:
            prerotations[len(prerotations.columns) + 1] = rotations
        return aligned, prerotations

    aligned = numpy.stack(
        Parallel(n_jobs=-1)(
            delayed(align_particle)(polar_refs, parts[i])
            for i in tqdm(range(len(parts)))
        )
    )
    gc.collect()
    return aligned


def normalize_image(image):
    """
    Normaization such that mean = 0, std = 1. 
    """
    return (image - image.mean()) / image.std()


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
    mask = create_circular_mask(
        stack.shape[-2], stack.shape[-1], radius=radius, soft_mask=soft_mask
    )
    for i in range(len(stack)):
        stack[i] = mask * stack[i]
    return stack


def center_image(image, mask=1):
    """
    Image centering with normalization, masking, and CoM calculation.
    Returns the orgininal image shifted. 
    """
    # Process image for center calculation
    normalized = normalize_image(image)
    positive_array = normalized.copy()
    positive_array[positive_array <= 0] = 0
    masked_positive = positive_array * mask
    cy, cx = center_of_mass(masked_positive)
    y_shift, x_shift = image.shape[0] / 2 - cy, image.shape[1] / 2 - cx
    # shift the orgininal image
    centered = ndimage.shift(image, [y_shift, x_shift], mode="wrap")
    return centered


def center_stack(stack):
    return numpy.stack([center_image(stack[i]) for i in range(len(stack))])


def process_image(image, mask=1):
    """
    Center, mask, and normalize image. 
    """
    centered = center_image(image, mask)
    processed = normalize_image(mask * centered)
    return processed


def process_stack(stack):
    """
    Center, mask, and normalize stack.
    """
    print("Processing stack...")
    mask = create_circular_mask(stack.shape[-2], stack.shape[-1])
    processed = numpy.stack(
        Parallel(n_jobs=-1)(
            delayed(process_image)(stack[i], mask) for i in tqdm(range(len(stack)))
        )
    )
    gc.collect()
    return processed


def warp_stack(stack):
    polar_stack = [None] * len(stack)
    for i in range(len(stack)):
        polar_stack[i] = warp_polar(stack[i])
    polar_stack = numpy.stack(polar_stack)
    return polar_stack


def stack_self_sort(stack, order_list=False):
    N = len(stack)
    polar_stack = warp_stack(stack)
    error_matrix = numpy.zeros((N, N))
    error_sums = []
    print("Sorting stack...")
    for i in tqdm(range(N - 1)):
        for j in range(i + 1, N):
            s, e, p = phase_cross_correlation(
                polar_stack[j], polar_stack[i], normalization=None
            )
            error_matrix[i, j], error_matrix[j, i] = e, e
    for i in range(N):
        error_sums += [[i, stack[i], (error_matrix[i] ** 0.25).sum()]]
    sorted_stack = numpy.stack([a[1] for a in sorted(error_sums, key=lambda l: l[2])])
    if order_list:
        sorted_list = [a[0] for a in sorted(error_sums, key=lambda l: l[2])]
        return sorted_list, sorted_stack
    return sorted_stack


def stack_self_align(stack, n=10):
    """ Establish global alignment of stack, where n is the number of iterations."""
    print("Aligning stack...")
    N = len(stack)
    aligned = stack.copy()
    polar = numpy.stack([warp_polar(aligned[i]) for i in range(N)])
    avgs = []
    rotations = numpy.zeros(N)
    for _ in tqdm(range(n)):
        avg = aligned.sum(axis=0)
        avgs.append(avg)
        avg_polar = warp_polar(avg)
        for i in range(N):
            cls_polar = polar[i]
            s, e, p = phase_cross_correlation(avg_polar, cls_polar, normalization=None)
            theta = round(s[0])
            polar[i] = numpy.roll(polar[i], theta, axis=0)
            rotations[i] += -theta
            aligned[i] = rotate(stack[i], rotations[i])
    return aligned  # , avgs


@profile
def stack_organize(stack):
    """ Sort, align, and process stack. """
    sorted_stack = stack_self_sort(stack)
    aligned_stack = stack_self_align(sorted_stack)
    final_stack = process_stack(aligned_stack)
    return final_stack


# =====================


class TopologyRepScript(appionScript.AppionScript):

    # =====================
    def setupParserOptions(self):
        self.parser.set_usage("Usage: %prog --stack=ID --start=# --end=# [options]")
        self.parser.add_option(
            "-N",
            "--num-part",
            dest="numpart",
            type="int",
            help="Number of particles to use",
            metavar="#",
        )
        self.parser.add_option(
            "-s",
            "--stack",
            dest="stackid",
            type="int",
            help="Stack database id",
            metavar="ID#",
        )

        self.parser.add_option(
            "--msaproc",
            dest="msaproc",
            type="int",
            default=1,
            help="Number of processor to use for CAN",
            metavar="#",
        )

        self.parser.add_option(
            "--lowpass",
            "--lp",
            dest="lowpass",
            type="int",
            help="Low pass filter radius (in Angstroms)",
            metavar="#",
        )
        self.parser.add_option(
            "--highpass",
            "--hp",
            dest="highpass",
            type="int",
            help="High pass filter radius (in Angstroms)",
            metavar="#",
        )
        self.parser.add_option(
            "--bin",
            dest="bin",
            type="int",
            default=1,
            help="Bin images by factor",
            metavar="#",
        )
        self.parser.add_option(
            "-i",
            "--iter",
            dest="iter",
            type="int",
            default=20,
            help="Number of iterations",
            metavar="#",
        )
        self.parser.add_option(
            "--start",
            dest="start",
            type="int",
            help="number of classes to create in first iteration",
        )
        self.parser.add_option(
            "--end",
            dest="end",
            type="int",
            help="number of classes to create in last iteration",
        )
        self.parser.add_option(
            "--mask",
            dest="mask",
            type="int",
            metavar="#",
            help="radius of circular mask to apply in pixels (default=(boxsize/2)-2)",
        )
        self.parser.add_option(
            "--itermult",
            dest="itermult",
            type="float",
            metavar="FLOAT",
            default=10.0,
            help="multiplier for determining number of times data will be presented to the network. Number of particles in your stack will by multiplied by this value to determine # of iterations",
        )
        self.parser.add_option(
            "--learn",
            dest="learn",
            type="float",
            metavar="FLOAT",
            default=0.01,
            help="direct learning rate - fraction that closest unit image will be moved toward presented data, 0.01 suggested for cryo, higher for neg stain",
        )
        self.parser.add_option(
            "--ilearn",
            dest="ilearn",
            type="float",
            metavar="FLOAT",
            default=0.0005,
            help="indirect learning rate - fraction that connection unit images will be moved should be lower than direct rate",
        )
        self.parser.add_option(
            "--age",
            dest="maxage",
            type="int",
            metavar="INT",
            default=25,
            help="number of iterations an edge connecting two units can be unused before it's discarded",
        )

        ### IMAGIC MSA options
        self.parser.add_option(
            "--msaiter",
            dest="msaiter",
            type="int",
            default=50,
            help="number of MSA iterations",
        )
        self.parser.add_option(
            "--numeigen",
            dest="numeigen",
            type="int",
            default=20,
            help="total number of eigen images to calculate",
        )
        self.parser.add_option(
            "--overcorrection",
            dest="overcorrection",
            type="float",
            default=0.8,
            help="overcorrection facter (0-1)",
        )
        self.parser.add_option(
            "--activeeigen",
            dest="activeeigen",
            type="int",
            default=10,
            help="number of active eigen images to use for classification",
        )

        ### true/false
        self.parser.add_option(
            "--keep-all",
            dest="keepall",
            default=False,
            action="store_true",
            help="Keep all intermediate node images",
        )
        self.parser.add_option(
            "--premask",
            dest="premask",
            default=False,
            action="store_true",
            help="Mask raw particles before processing",
        )
        self.parser.add_option(
            "--no-mask",
            dest="nomask",
            default=False,
            action="store_true",
            help="Do not apply a mask to the class averages",
        )
        self.parser.add_option(
            "--no-center",
            dest="nocenter",
            default=False,
            action="store_true",
            help="Do not center particles after each iteration",
        )
        self.parser.add_option(
            "--classiter",
            dest="classiter",
            default=False,
            action="store_true",
            help="Perform iterative averaging of class averages",
        )
        self.parser.add_option(
            "--uploadonly",
            dest="uploadonly",
            default=False,
            action="store_true",
            help="Just upload results of completed run",
        )
        self.parser.add_option(
            "--invert",
            dest="invert",
            default=False,
            action="store_true",
            help="Invert before alignment",
        )

        ### choices
        self.mramethods = ("eman", "imagic", "python")
        self.parser.add_option(
            "--mramethod",
            dest="mramethod",
            help="Method for multi-reference alignment",
            metavar="PACKAGE",
            type="choice",
            choices=self.mramethods,
            default="python",
        )
        self.msamethods = ("can", "imagic")
        self.parser.add_option(
            "--msamethod",
            dest="msamethod",
            help="Method for MSA",
            metavar="PACKAGE",
            type="choice",
            choices=self.msamethods,
            default="can",
        )
        self.storagemethods = ("memory", "disk")
        self.parser.add_option(
            "--storagemethod",
            dest="storagemethod",
            help="Keep stacks in memory or write to disk.",
            type="choice",
            choices=self.storagemethods,
            default="disk",
        )

    # =====================
    def checkConflicts(self):
        if self.params["stackid"] is None:
            apDisplay.printError("stack id was not defined")
        if self.params["start"] is None:
            apDisplay.printError("a number of starting classes was not provided")
        if self.params["end"] is None:
            apDisplay.printError("a number of ending classes was not provided")
        if self.params["runname"] is None:
            apDisplay.printError("run name was not defined")
        self.stackdata = apStack.getOnlyStackData(self.params["stackid"], msg=False)
        stackfile = os.path.join(self.stackdata["path"]["path"], self.stackdata["name"])
        # check for virtual stack
        self.params["virtualdata"] = None
        if not os.path.isfile(stackfile):
            vstackdata = apStack.getVirtualStackParticlesFromId(self.params["stackid"])
            npart = len(vstackdata["particles"])
            self.params["virtualdata"] = vstackdata
        else:
            npart = apFile.numImagesInStack(stackfile)

        if self.params["numpart"] is None:
            self.params["numpart"] = npart
        elif self.params["numpart"] > npart:
            apDisplay.printError(
                "trying to use more particles "
                + str(self.params["numpart"])
                + " than available "
                + str(apFile.numImagesInStack(stackfile))
            )

        self.boxsize = apStack.getStackBoxsize(self.params["stackid"])
        self.workingboxsize = math.floor(self.boxsize / self.params["bin"])
        if not self.params["mask"]:
            self.params["mask"] = (self.boxsize / 2) - 2
        self.workingmask = math.floor(self.params["mask"] / self.params["bin"])
        # if self.params['mramethod'] == 'imagic':
        #     self.imagicroot = apIMAGIC.checkImagicExecutablePath()
        #     self.imagicversion = apIMAGIC.getImagicVersion(self.imagicroot)

    # =====================
    def setRunDir(self):
        path = self.stackdata["path"]["path"]
        uppath = os.path.abspath(os.path.join(path, "../.."))
        uppath = string.replace(uppath, "/jetstor/APPION", "")
        self.params["rundir"] = os.path.join(uppath, "align", self.params["runname"])

    # =====================
    def dumpParameters(self):
        self.params["runtime"] = time.time() - self.t0
        self.params["timestamp"] = self.timestamp
        paramfile = "topolrep-" + self.timestamp + "-params.pickle"
        pf = open(paramfile, "wb")
        pickle.dump(self.params, pf)
        pf.close()

    # =====================
    def insertTopolRepJob(self):
        topoljobq = appiondata.ApTopolRepJobData()
        topoljobq["runname"] = self.params["runname"]
        topoljobq["path"] = appiondata.ApPathData(
            path=os.path.abspath(self.params["rundir"])
        )
        topoljobdatas = topoljobq.query(results=1)
        if topoljobdatas:
            alignrunq = appiondata.ApAlignRunData()
            alignrunq["runname"] = self.params["runname"]
            alignrunq["path"] = appiondata.ApPathData(
                path=os.path.abspath(self.params["rundir"])
            )
            alignrundata = alignrunq.query(results=1)
            if topoljobdatas[0]["finished"] is True or alignrundata:
                apDisplay.printError(
                    "This run name already exists as finished in the database, please change the runname"
                )
        topoljobq[
            "REF|projectdata|projects|project"
        ] = apProject.getProjectIdFromStackId(self.params["stackid"])
        topoljobq["timestamp"] = self.timestamp
        topoljobq["finished"] = False
        topoljobq["hidden"] = False
        if self.params["commit"] is True:
            topoljobq.insert()
        self.params["topoljob"] = topoljobq
        return

    # =====================
    def insertRunIntoDatabase(self):
        apDisplay.printMsg("Inserting Topology Rep Run into DB")

        ### set up alignment run
        alignrunq = appiondata.ApAlignRunData()
        alignrunq["runname"] = self.params["runname"]
        alignrunq["path"] = appiondata.ApPathData(
            path=os.path.abspath(self.params["rundir"])
        )
        uniquerun = alignrunq.query(results=1)
        if uniquerun:
            apDisplay.printError(
                "Run name '"
                + self.params["runname"]
                + "' and path already exist in database"
            )

        ### set up topology rep run
        toprepq = appiondata.ApTopolRepRunData()
        toprepq["runname"] = self.params["runname"]
        toprepq["mask"] = self.params["mask"]
        toprepq["itermult"] = self.params["itermult"]
        toprepq["learn"] = self.params["learn"]
        toprepq["ilearn"] = self.params["ilearn"]
        toprepq["age"] = self.params["maxage"]
        toprepq["mramethod"] = self.params["mramethod"]
        toprepq["job"] = self.params["topoljob"]

        ### finish alignment run
        alignrunq["topreprun"] = toprepq
        alignrunq["hidden"] = False
        alignrunq["runname"] = self.params["runname"]
        alignrunq["description"] = self.params["description"]
        alignrunq["lp_filt"] = self.params["lowpass"]
        alignrunq["hp_filt"] = self.params["highpass"]
        alignrunq["bin"] = self.params["bin"]
        ### set up alignment stack
        alignstackq = appiondata.ApAlignStackData()
        alignstackq["imagicfile"] = "mrastack.mrcs"
        alignstackq["avgmrcfile"] = "average.mrc"
        alignstackq["refstackfile"] = os.path.basename(self.params["currentcls"])
        alignstackq["iteration"] = self.params["currentiter"]
        alignstackq["path"] = appiondata.ApPathData(
            path=os.path.abspath(self.params["rundir"])
        )
        alignstackq["alignrun"] = alignrunq

        ### check to make sure files exist
        mrcsfile = os.path.join(self.params["rundir"], alignstackq["imagicfile"])
        if not os.path.isfile(mrcsfile):
            apDisplay.printError("could not find stack file: " + mrcsfile)
        avgmrcfile = os.path.join(self.params["rundir"], alignstackq["avgmrcfile"])
        if not os.path.isfile(avgmrcfile):
            apDisplay.printError("could not find average mrc file: " + avgmrcfile)
        refstackfile = os.path.join(self.params["rundir"], alignstackq["refstackfile"])
        if not os.path.isfile(refstackfile):
            apDisplay.printError("could not find reference stack file: " + refstackfile)

        alignstackq["stack"] = self.stackdata
        alignstackq["boxsize"] = math.floor(self.workingboxsize)
        alignstackq["pixelsize"] = self.stack["apix"] * self.params["bin"]
        alignstackq["description"] = self.params["description"]
        alignstackq["hidden"] = False
        alignstackq["num_particles"] = self.params["numpart"]

        if self.params["commit"] is True:
            alignstackq.insert()
        self.alignstackdata = alignstackq

    # =====================
    def insertParticlesIntoDatabase(self, partlist, partrefdict):
        # insert particle alignment information into database
        count = 0
        t0 = time.time()
        apDisplay.printColor(
            "\nPreparing to insert particle alignment data, please wait", "cyan"
        )

        # get path data
        pathq = appiondata.ApPathData()
        pathq["path"] = os.path.abspath(self.params["rundir"])
        pathdata = pathq.query(results=1)
        pathid = pathdata[0].dbid

        # align run id
        alignrunid = self.alignstackdata["alignrun"].dbid

        # get stack particle ids
        stackpdbdict = {}
        sqlcmd = (
            "SELECT particleNumber,DEF_id "
            + "FROM ApStackParticleData "
            + "WHERE `REF|ApStackData|stack`=%i" % (self.params["stackid"])
        )
        results = sinedon.directq.complexMysqlQuery("appiondata", sqlcmd)

        for part in results:
            pnum = int(part["particleNumber"])
            stackpdbdict[pnum] = int(part["DEF_id"])

        apDisplay.printColor(
            "found "
            + str(len(results))
            + " particles in "
            + apDisplay.timeString(time.time() - t0),
            "cyan",
        )

        t0 = time.time()
        apDisplay.printColor("\nInserting class averages into database", "cyan")
        # insert reference image data
        reflistvals = []
        for i in range(1, max(partrefdict.values()) + 1):
            sqlvals = "(%i,%i,'%s',%i,%i)" % (
                i,
                self.params["currentiter"],
                os.path.basename(self.params["currentcls"]),
                alignrunid,
                pathid,
            )
            reflistvals.append(sqlvals)

        sqlcmd = (
            "INSERT INTO `ApAlignReferenceData` ("
            + "`refnum`,`iteration`,`mrcsfile`,"
            + "`REF|ApAlignRunData|alignrun`,`REF|ApPathData|path`) "
        )
        sqlcmd += "VALUES " + ",".join(reflistvals)
        sinedon.directq.complexMysqlQuery("appiondata", sqlcmd)

        # get DEF_ids from inserted references
        refq = appiondata.ApAlignReferenceData()
        refq["iteration"] = self.params["currentiter"]
        refq["mrcsfile"] = os.path.basename(self.params["currentcls"])
        refq["path"] = appiondata.ApPathData(
            path=os.path.abspath(self.params["rundir"])
        )
        refq["alignrun"] = self.alignstackdata["alignrun"]
        refresults = refq.query()

        # save DEF_ids to dictionary
        refdbiddict = {}
        for ref in refresults:
            refdbiddict[ref["refnum"]] = ref.dbid

        apDisplay.printColor(
            "inserted "
            + str(len(refdbiddict))
            + " class averages in "
            + apDisplay.timeString(time.time() - t0),
            "cyan",
        )

        t0 = time.time()
        apDisplay.printColor("\nAssembling database insertion command", "cyan")
        partlistvals = []

        for partdict in partlist:
            count += 1
            if count % (len(partlist) / 100) == 0:
                pleft = int(float(count) / len(partlist) * 100)
                perpart = (time.time() - t0) / count
                tleft = (len(partlist) - count) * perpart
                sys.stderr.write(
                    "%3i%% complete, %s left    \r"
                    % (pleft, apDisplay.timeString(tleft))
                )

            partnum = int(partdict["partnum"])
            refnum = partrefdict[partnum]
            refnum_dbid = refdbiddict[refnum]
            stackpart_dbid = stackpdbdict[partnum]

            sqlvals = "(%i,%i,%i,%s,%s,%s,%i,%s,%i)" % (
                partdict["partnum"],
                alignrunid,
                stackpart_dbid,
                partdict["xshift"],
                partdict["yshift"],
                partdict["inplane"],
                partdict["mirror"],
                partdict["cc"],
                refnum_dbid,
            )

            partlistvals.append(sqlvals)

        sys.stderr.write("100% complete\t\n")

        apDisplay.printColor("Inserting particle information into database", "cyan")

        # start big insert cmd
        sqlstart = (
            "INSERT INTO `ApAlignParticleData` ("
            + "`partnum`,`REF|ApAlignStackData|alignstack`,"
            + "`REF|ApStackParticleData|stackpart`,"
            + "`xshift`,`yshift`,`rotation`,`mirror`,"
            + "`correlation`,`REF|ApAlignReferenceData|ref`) "
            + "VALUES "
        )

        # break up command into groups of 100K inserts
        # this is a workaround for the max_allowed_packet at 16MB
        n = 100000
        sqlinserts = [partlistvals[i : i + n] for i in range(0, len(partlistvals), n)]

        for sqlinsert in sqlinserts:
            sqlcmd = sqlstart + ",".join(sqlinsert)
            sinedon.directq.complexMysqlQuery("appiondata", sqlcmd)

        apDisplay.printColor(
            "\nInserted "
            + str(count)
            + " particles into the database in "
            + apDisplay.timeString(time.time() - t0),
            "cyan",
        )

    # =====================
    def writeTopolRepLog(self, text):
        f = open("topolrep.log", "a")
        f.write(apParam.getLogHeader())
        f.write(text + "\n")
        f.close()

    # =====================
    def getCANPath(self):
        unames = os.uname()
        if unames[-1].find("64") >= 0:
            exename = "can64_mp.exe"
        else:
            exename = "can32.exe"
        CANexe = apParam.getExecPath(exename, die=True)
        return CANexe

    @profile
    def runCAN(self):
        numIters = int(self.params["numpart"] * self.params["itermult"])
        decrement = self.params["start"] - self.params["end"]
        if self.params["iter"] > 0:
            decrement /= float(self.params["iter"])
        if self.params["currentiter"] == 0:
            stackfile = self.stack["file"]
        else:
            if self.params["storagemethod"] == "memory":
                stackfile = "numpy stack"
            elif self.params["storagemethod"] == "disk":
                stackfile = self.params["alignedstack"]
        numClasses = self.params["start"] - (decrement * self.params["currentiter"])
        canopts = "%s classes %i %.3f %.5f %i %i" % (
            stackfile,
            numIters,
            self.params["learn"],
            self.params["ilearn"],
            self.params["maxage"],
            numClasses,
        )
        can_params = {key: self.params[key] for key in ["learn", "ilearn", "maxage"]}
        can_params["numpres"] = numIters
        can_params["numClasses"] = numClasses

        outfile = "classes"

        apDisplay.printMsg("running CAN:")
        print("CAN parameters:")
        for key in can_params:
            print(key, "=", can_params[key])
        if self.params["currentiter"] == 0:
            # If it is the first time executing CAN, then read the .star stack file, and process the particles
            process_params = {  # should be self.stack['...']
                key: self.params[key]
                for key in ["apix", "lowpass", "highpass", "premask", "bin", "invert"]
            }
            process_params[
                "normalization"
            ] = True  # True uses default boxnorm, see imagenorm and apCAN for details

            print("\nParticle preprocessing parameters:")
            for key in process_params:
                print(f"{key} = {process_params[key]}")

            can_output = apCAN.CAN(
                self.stack["file"],
                outfile,
                can_params,
                process_params,
                return_parts=True,
            )

            print("\n CAN execution complete.")

            self.orig_stack = can_output["particles"]
            self.classes = can_output["classes"]
            del can_output

            gc.collect()

            raise Exception

            self.rotations = pd.DataFrame()

            if self.params["storagemethod"] == "disk":
                print("Writing stack data to disk...")
                # raise Exception
                del self.classes
                mrc.write(self.orig_stack, self.params["localstack"])
                del self.orig_stack
                self.rotations.to_csv(self.params["rotations"])
                del self.rotations

            gc.collect()

        else:
            # pass the existing particle stack (np.array) to CAN for all other iterations
            if self.params["storagemethod"] == "memory":
                self.classes = apCAN.CAN(
                    self.aligned, outfile, can_params, return_parts=True
                )["classes"]
            elif self.params["storagemethod"] == "disk":
                apCAN.CAN(self.params["alignedstack"], outfile, can_params)

            gc.collect()

        self.params["currentnumclasses"] = numClasses

        self.writeTopolRepLog(canopts)  # needs to be updated

        # check that CAN ran properly
        if not os.path.exists("classes.mrcs"):
            apDisplay.printError(
                "CAN did not create an output stack, check CAN functionality"
            )

        # tar spider files
        spitar = tarfile.open("cls.spi.tar", "w")
        spifiles = glob.glob("classes_class_*.spi")
        for spif in spifiles:
            spitar.add(spif)
        spitar.close()
        # remove class files
        for spif in spifiles:
            os.remove(spif)

        # align resulting classes
        self.alignClassAvgs()

    def alignClassAvgs(self):
        classname = "classes.mrcs"
        aligned = None
        if self.params["currentiter"] < self.params["iter"]:
            if self.params["storagemethod"] == "memory":
                unaligned = self.classes
            elif self.params["storagemethod"] == "disk":
                unaligned = mrc.read(classname)
            processed = process_stack(unaligned)
            aligned, log = stack_organize(processed)
            if self.params["storagemethod"] == "memory":
                self.classes = aligned

        outputcls = os.path.join(
            self.params["rundir"], "classes%02i.mrcs" % self.params["currentiter"]
        )

        if aligned is not None:
            mrc.write(aligned, outputcls)
        else:
            cmd = f"mv {classname} {outputcls}"
            os.system(cmd)

        self.params["currentcls"] = outputcls

    # =====================
    def TarExtractall(self, tarobj):
        """
        Function introduced in python 2.5 and is not available in python 2.4
        Copied and modified from python 2.6 code 
        Delete this when we move to python 2.5 code - Neil

        Extract all members from the archive to the current working
        directory and set owner, modification time and permissions on
        directories afterwards. `path' specifies a different directory
        to extract to. `members' is optional and must be a subset of the
        list returned by getmembers().
        """
        import copy
        import operator

        directories = []
        members = tarobj.getmembers()

        for tarinfo in members:
            if tarinfo.isdir():
                # Extract directories with a safe mode.
                directories.append(tarinfo)
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 0o700
            tarobj.extract(tarinfo, ".")

        # Reverse sort directories.
        directories.sort(key=operator.attrgetter("name"))
        directories.reverse()

        # Set correct owner, mtime and filemode on directories.
        for tarinfo in directories:
            dirpath = os.path.join(".", tarinfo.name)
            tarobj.chown(tarinfo, dirpath)
            tarobj.utime(tarinfo, dirpath)
            tarobj.chmod(tarinfo, dirpath)

    # =====================
    def readPartRotations(self):
        ## create an array of particle information
        pinfo = []

        # get particle information from rotation dataframe
        rotations = self.get_rotations()
        if type(rotations) == str:
            rotations = pd.read_csv(rotations)

        # store contents in array
        for i in range(len(rotations)):
            pdata = {}

            pdata["partnum"] = i + 1
            pdata["inplane"] = rotations.iloc[i].sum()
            pdata["xshift"] = 0  # numlist[3]
            pdata["yshift"] = 0  # -numlist[2]
            pdata["cc"] = 0
            pdata["mirror"] = 0
            pinfo.append(pdata)

        return pinfo

    # =====================
    def canClassificationToDict(self):
        ### read the particle classification results from CAN
        ### output in spider format & save as a dictionary
        pclass = {}
        spitarf = "cls.spi.tar"
        if not os.path.isfile(spitarf):
            apDisplay.printError("no SPIDER cls tar file found")
        spitar = tarfile.open(spitarf)

        ## revert when using python 2.5+
        self.TarExtractall(spitar)
        # spitar.extractall()

        spitar.close()
        spifiles = glob.glob("classes_class_*.spi")
        if not spifiles:
            apDisplay.printError("CAN did not create SPIDER cls files")

        spifiles.sort()

        # store classification in dictionary, defined by particle number
        for spi in spifiles:
            ## get ref number from class file name
            refn = int(os.path.splitext(spi)[0][-4:])
            f = open(spi)
            for l in f:
                if l[:2] == " ;":
                    continue
                spidict = operations.spiderInLine(l)
                p = int(spidict["floatlist"][0])
                if p not in pclass:
                    pclass[p] = self.sortedAvgDict[refn]
                else:
                    apDisplay.printError(
                        "particle %i has more than 1 classification,"
                        + " classified to reference %i and %i" % (p, pclass[p], refn)
                    )
            f.close()
            os.remove(spi)
        return pclass

    # =====================
    def sortFinalAverages(self):
        ### sort class averages using cross correlation
        apDisplay.printMsg("Sorting final class averages")

        # read stack
        # sort stack
        # save ordered stack (remove old)
        # write dictionary with old indices as keys and new order (from 1) as val

        self.sortedAvgDict = {}

        # read class averages
        unaligned = mrc.read(self.params["currentcls"])
        # center, mask, and normalize particles
        processed = process_stack(unaligned)
        # sort
        self.sortedList, sorted_stack = stack_self_sort(processed, order_list=True)
        del processed
        final_stack = process_stack(stack_self_align(sorted_stack))
        mrc.write(final_stack, self.params["currentcls"])
        del final_stack

        self.sortedAvgDict = [
            self.sortedList[i] + 1 for i in range(len(self.sortedList))
        ]
        self.sortedAvgDict = dict(
            zip(self.sortedAvgDict, range(1, len(self.sortedAvgDict) + 1))
        )

        final_stack_unproc = []
        for i in range(len(self.sortedList)):
            j = self.sortedList[i]
            final_stack_unproc.append(unaligned[j])

        final_stack_unproc = mask_stack(numpy.stack(final_stack_unproc))
        outcls = self.params["rundir"] + "/classes_avg.mrcs"
        mrc.write(final_stack_unproc, outcls)
        self.params["currentcls"] = outcls

        return

    # #=====================
    def applySort(self):
        out = "classes_avg.mrcs"
        # read class averages
        avgfile = os.path.join(self.params["iterdir"], "classes.mrcs")
        mrc.write(process_stack(mrc.read(avgfile)), out)

    # =====================
    def get_classes(self):
        if self.params["storagemethod"] == "disk":
            return self.params["currentcls"]
        elif self.params["storagemethod"] == "memory":
            return self.classes
        else:
            print("Storage method not set as memory or disk")
            return None

    # =====================
    def get_stack(self):
        if self.params["storagemethod"] == "disk":
            return self.params["localstack"]
        elif self.params["storagemethod"] == "memory":
            return self.orig_stack
        else:
            print("Storage method not set as memory or disk")
            return None

    # =====================
    def get_rotations(self):
        if self.params["storagemethod"] == "disk":
            return self.params["rotations"]
        elif self.params["storagemethod"] == "memory":
            return self.rotations
        else:
            print("Storage method not set as memory or disk")
            return None

    # =====================
    def start(self):
        mem = None
        index = "start"
        mem = record_memory(mem, index)
        self.insertTopolRepJob()
        self.stack = {}
        self.stack["apix"] = apStack.getStackPixelSizeFromStackId(
            self.params["stackid"]
        )
        self.params["apix"] = self.stack["apix"]
        if self.params["virtualdata"] is not None:
            self.stack["file"] = self.params["virtualdata"]["filename"]
        else:
            self.stack["file"] = os.path.join(
                self.stackdata["path"]["path"], self.stackdata["name"]
            )
        self.dumpParameters()

        log_file = f"{self.params['rundir']}/memLog_{self.params['storagemethod']}.log"
        logging.basicConfig(filename=log_file, level=logging.INFO)

        ### process stack to local file
        self.params["localstack"] = os.path.join(
            self.params["rundir"], self.timestamp + ".mrcs"
        )
        ### set rotation file for particle rotations during alignment
        self.params["rotations"] = os.path.join(self.params["rundir"], "rotations.csv")

        ### The preprocessing steps below have been integrated into apCAN.CAN()
        # self.params["canexe"] = self.getCANPath()
        # processImgList = []
        # ### check for Relion star file
        # if self.stack["file"].endswith(".star"):
        #     processImgList = apRelion.getMrcParticleFilesFromStar(self.stack["file"])
        #     self.numparts_dict = {}
        #     for pimg in processImgList:
        #         with open(self.stack["file"]) as file:
        #             s = 0
        #             i = 0
        #             for line in file:
        #                 img = pimg.split("micrographs/")[1]
        #                 if img in line:
        #                     s += 1
        #             self.numparts_dict[pimg] = s
        # else:
        #     processImgList.append(self.stack["file"])
        # for pimg in processImgList:
        #     a = proc2dLib.RunProc2d()
        #     a.setValue("infile", pimg)
        #     a.setValue("outfile", self.params["localstack"])
        #     a.setValue("apix", self.stack["apix"])
        #     print(self.stack['apix'])
        #     a.setValue("bin", self.params["bin"])
        #     if self.stack["file"].endswith("star"):
        #         a.setValue("last", self.numparts_dict[pimg] - 1)
        #     else:
        #         a.setValue("last", self.params["numpart"] - 1)
        #     a.setValue("append", True)

        #     if self.params["lowpass"] is not None and self.params["lowpass"] > 1:
        #         a.setValue("lowpass", self.params["lowpass"])
        #     if self.params["highpass"] is not None and self.params["highpass"] > 1:
        #         a.setValue("highpass", self.params["highpass"])
        #     if self.params["invert"] is True:
        #         a.setValue("invert", True)
        #     if self.params["premask"] is True and self.params["mramethod"] != "imagic":
        #         a.setValue("mask", self.params["mask"])

        #     if self.params["virtualdata"] is not None:
        #         vparts = self.params["virtualdata"]["particles"]
        #         plist = [int(p["particleNumber"]) - 1 for p in vparts]
        #         a.setValue("list", plist)

        #     if self.params["uploadonly"] is not True:
        #         if os.path.isfile(os.path.join(self.params["rundir"], "stack.hed")):
        #             self.params["localstack"] = os.path.join(
        #                 self.params["rundir"], "stack.hed"
        #             )
        #             break
        #         else:
        #             a.run()

        # if self.params["numpart"] != apFile.numImagesInStack(self.params["localstack"]):
        #     print(
        #         self.params["numpart"],
        #         " ",
        #         apFile.numImagesInStack(self.params["localstack"]),
        #     )
        #     apDisplay.printError("Missing particles in stack")

        # ### mask particles before alignment
        # if self.params["premask"]:
        #     # convert mask to fraction for imagic
        #     particles_orig = mrc.read(self.params["localstack"])
        #     shutil.move(
        #         self.params["localstack"],
        #         self.params["localstack"].replace(".mrcs", "_orig.mrcs"),
        #     )
        #     masked = mask_stack(particles_orig)
        #     mrc.write(masked, self.params["localstack"])
        #     del particles_orig, masked

        # origstack = self.params["localstack"]
        ### end comtest

        ### find number of processors
        #         if self.params['nproc'] is None:
        self.params["nproc"] = apParam.getNumProcessors()

        if self.params["uploadonly"] is not True:
            aligntime = time.time()
            # run through iterations
            for i in range(0, self.params["iter"] + 1):
                # move back to starting directory
                os.chdir(self.params["rundir"])

                # set up next iteration directory
                self.params["currentiter"] = i
                self.params["iterdir"] = os.path.abspath("iter%02i" % i)
                self.params["iterdir"] = self.params["iterdir"].replace(
                    "/jetstor/APPION", ""
                )
                if os.path.exists(self.params["iterdir"]):
                    apDisplay.printError(
                        "Error: directory '%s' exists, aborting alignment"
                        % self.params["iterdir"]
                    )

                # create directory for iteration
                os.makedirs(self.params["iterdir"])
                os.chdir(self.params["iterdir"])

                index = "preCAN-" + str(i)
                # if at first iteration, create initial class averages
                if i == 0:
                    self.params["alignedstack"] = (
                        os.path.splitext(self.params["localstack"])[0] + "_aligned.mrcs"
                    )
                    # self.alignedstack = mrc.read(self.params["alignedstack"])
                    mem = record_memory(mem, index)
                    x, log = self.runCAN()
                    logging.log(20, log)
                    continue

                # MRA -- align particles to existing class averages
                index = index.replace("CAN", "MRA")
                mem = record_memory(mem, index)
                (self.aligned, self.rotations), log = align_stack(
                    self.get_classes(),
                    self.get_stack(),
                    self.get_rotations(),
                    return_rotations=True,
                )
                logging.log(20, log)
                if self.params["storagemethod"] == "disk":
                    mrc.write(self.aligned, self.params["alignedstack"])
                    del self.aligned
                    self.rotations.to_csv(self.params["rotations"])
                    del self.rotations

                # MSA -- create class averages from aligned stack
                index = "preCAN-" + str(i)
                mem = record_memory(mem, index)
                x, log = self.runCAN()
                logging.log(20, log)
                index = "postCAN-" + str(i)
            mem = record_memory(mem, index)
            aligntime = time.time() - aligntime
            time_msg = "Alignment time: " + apDisplay.timeString(aligntime)
            logging.log(20, time_msg)
            apDisplay.printMsg(time_msg)

        ## set upload information params:
        else:
            ## get last iteration
            alliters = glob.glob("iter*")
            alliters.sort()

            ## get iteration number from iter dir
            self.params["currentiter"] = int(alliters[-1][-2:])
            self.params["iterdir"] = os.path.join(self.params["rundir"], alliters[-1])
            self.params["currentcls"] = "classes%02i" % (self.params["currentiter"])

            ## go into last iteration directory
            os.chdir(self.params["iterdir"])
            self.params["alignedstack"] = os.path.abspath("mrastack")
            if os.path.isfile(
                os.path.join(self.params["rundir"], self.params["currentcls"] + ".mrcs")
            ):
                p1 = os.path.join(self.params["rundir"], self.params["currentcls"])
                p2 = os.path.join(self.params["iterdir"], self.params["currentcls"])
                shutil.move(p1, p2)

        ## sort the class averages
        self.sortFinalAverages()

        ### get particle information from last iteration
        partlist = self.readPartRotations()  # NEEDS TO BE ADDRESSED

        partrefdict = self.canClassificationToDict()

        # move back to starting directory
        os.chdir(self.params["rundir"])

        # move aligned stack to current directory for appionweb
        if not os.path.isfile("mrastack.mrcs"):
            if self.params["storagemethod"] == "memory":
                mrc.write(self.aligned, "mrastack.mrcs")
            elif self.params["storagemethod"] == "disk":
                shutil.move(self.params["alignedstack"], "mrastack.mrcs")
                cmd = f"rm {self.params['localstack']}"
                os.system(cmd)

        ### create an average mrc of final references
        if not os.path.isfile("average.mrc"):
            apStack.averageStack(stack=self.params["currentcls"])
            self.dumpParameters()

        ### save to database
        if self.params["commit"] is True:
            self.insertRunIntoDatabase()
            self.insertParticlesIntoDatabase(partlist, partrefdict)
        mem = record_memory(mem, index="end of start()", write=True)


# =====================
if __name__ == "__main__":
    topRep = TopologyRepScript()
    topRep.start()
    topRep.close()
