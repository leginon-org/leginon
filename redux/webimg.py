import os
import sys
import imp
import reduxconfig

# this namesapce should export one function:
#   path(str: mrc_path) -> str
# that returns the full path of a webimg jpg of an .mrc


class NotFound(Exception):
    def __init__(self, message):
        super(NotFound, self).__init__(message)


def noop(mrc):
    raise NotFound(mrc)


def _parts(path):
    # type :: (str) -> List[str]
    return os.path.normpath(path).split(os.sep)


def _legacy(mrc):
    # type :: (str) -> str
    jpg = mrc.replace("/leginon/", "/cache/")
    return jpg.replace(".mrc", ".jpg")


def _memc(mrc):
    # type :: (str) -> str
    # ex.
    #  mrc(gpfs): /gpfs/leginon/yshin/.../.../22jan13a/rawdata/file.mrc
    #  index:  0      1       2          3            -3           -2         -1
    #  parts: ["", "gpfs", "leginon", "yshin", ..., "22jan13a", "rawdata", "file.mrc"]
    #
    #  mrc(igloo): /h1/yshin/leginon/.../.../22jan13a/rawdata/file.mrc
    #  index:  0   1       2         3              -3           -2         -1
    #  parts: ["", "h1", "yshin", "leginon", ..., "22jan13a", "rawdata", "file.mrc"]
    parts = _parts(mrc)

    def user():
        if parts[1] in ("h1", "h2", "h3"):
            return parts[2]
        if parts[1] == "gpfs":
            return parts[3]
        raise Exception("webimg: invalid request [%s]" % mrc)

    def paths():
        """ lazily evaluate paths to try and find the jpg """
        basename, _ = os.path.splitext(parts[-1])
        # /memcweb/webimg.gpfs/yshin/22jan13a/rawdata/file.jpg
        yield os.path.join("/", "memcweb", "webimg.gpfs", user(), parts[-3],
                           "rawdata", basename + ".jpg")
        # /memcweb/webimg/22jan13a/file.jpg
        yield os.path.join("/", "memcweb", "webimg", parts[-3], basename + ".jpg")
        # fixme: until igloo migration finishes - /gpfs/cache/yshin/22jan13a/rawdata/file.jpg
        yield os.path.join("/", "gpfs", "cache", user(), parts[-3], "rawdata", basename + ".jpg")

    for jpg in paths():
        if os.path.exists(jpg):
            return jpg
        sys.stderr.write("  webimg: check [%s] -> enoent" % jpg)

    raise Exception("webimg: could not find a jpg for [%s]" % mrc)


def _nccat(mrc):
    # mrc(beegfs): /beegfs/leginon/dsashital/.../.../n21aug26c/rawdata/file.mrc
    #  index:  0      1       2          3               -3           -2         -1
    #  parts: ["", "beegfs", "leginon", "dsahital", ..., "22jan13a", "rawdata", "file.mrc"]
    parts = _parts(mrc)
    basename, _ = os.path.splitext(parts[-1])
    # /beegfs/cache/dsashital/n21aug26c/rawdata/file.jpg
    return os.path.join("/", "beegfs", "cache",
                        parts[3], parts[-3], "rawdata", basename + ".jpg")


def _init():
    # default export is legacy /gpfs behavior
    handler = "legacy"

    if "webimg.path" in reduxconfig.config:
        handler = reduxconfig.config["webimg.path"]

    if handler.startswith("file:"):
        sys.stderr.write("webimg: loading handler [%s]" % handler[5:])
        mod = imp.load_source("webimg.handler", handler[5:])
        return mod.path

    sys.stderr.write("webimg: setting handler to [%s]" % handler)
    return _route[handler]


_route = {
    "legacy": _legacy,
    "memc": _memc,
    "nccat": _nccat,
    "noop": noop,
}

path = _init()
