Without energe filter, K2 camera is often installed on an FEI scope with an entry in TEM User Interface Camera tab under another camera, for example BM-Falcon, or BM-Orius.

## If you have Ceta, and K2 under it pretends to be BM-Falcon:

Put them all on the same plane probably will work. By that I mean K2 pushes Ceta out when it needs to acquire. If not, try this:

    Ceta 50


On K2 computer

    GatanK2Counting 49
    GatanK2Super 49
    GatanK2Linear 49

-   In FEI software Falcon can push other camera out when it inserts.

## If you have Falcon, Ceta, and then K2 under them pretend to be BM-Orius:

### on FEI computer:

In your instruments.cfg, include

    [Fake Orius]
    class: tia.TIA_Orius
    zplane: 48
    width: 4096
    height: 4096

The zplane assignment for the cameras should be in this order

    Falcon 50
    Ceta 49
    Fake Orius 48

### On K2 computer,

Use your normal K2 instruments.cfg. Make sure K2 camera is assigned at the same zplane as the Falcon camera.

GatanK2Counting 50
GatanK2Super 50
GatanK2Linear 50

This make Falcon retracts when K2 is inserted, because they are on the same plane.
FEI software will retract Fake-Orius when it is asked to insert Falcon or Ceta from Leginon.
