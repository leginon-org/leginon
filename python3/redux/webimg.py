import sys
import imp
from redux import reduxconfig

# this namespace should export one function:
#   path(mrc_path: str) -> str
# that returns the full path of a webimg jpg of an .mrc


class NotFound(Exception):
    def __init__(self, message):
        super(NotFound, self).__init__(message)


def noop(mrc):
    raise NotFound(mrc)


def _legacy(mrc):
    # type :: (str) -> str
    jpg = mrc.replace("/leginon/", "/cache/")
    jpg = jpg.replace("/rawdata", "/")
    return jpg.replace(".mrc", ".jpg")


def _init():
    # default export is legacy behavior
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
    "noop": noop,
}

path = _init()
