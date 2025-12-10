## Adjust Target For Drift Check Box is now a choice

If you checked "adjust target for drift" in any node of Acquisition class, it should be
changed to select "one" ancestor. A python script "update16.py" is provided for a complete
update of such setting in all related nodes. If the drift is so large that the different
versions of the parent images can not be correlated, you should change the choice from "one"
to "all" ancestors.
