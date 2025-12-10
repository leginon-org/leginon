When something goes wrong with Leginon's communication with the TEM or camera, it is often most helpful to test the low level interface to the instrument. For example, on the FEI TEM host computer, start Python and run the following to get the current magnification:

    import pyscope.fei
    s = pyscope.fei.Tecnai()
    s.getMagnification()
