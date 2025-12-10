Since there are reports of disagreement of camera frame configuration vs sum unaligned image returned to Leginon, and the behavior changes with too many factors, a direct overwrite is now possible by making the assignment within dmsem.cfg

To do this, copy these from pyscope/dmsem.cfg.template to your dmsem.cfg used by K2/K3.

    OVERWRITE_FRAME_ORIENTATION =False
    FRAME_FLIP_TO_OVERWRITE_WITH = True

Shown above is the default. You should test it out. If that gives you a flip in the aligned image through Appion frame alignment, Change this to

    OVERWRITE_FRAME_ORIENTATION =True
    FRAME_FLIP_TO_OVERWRITE_WITH = False
