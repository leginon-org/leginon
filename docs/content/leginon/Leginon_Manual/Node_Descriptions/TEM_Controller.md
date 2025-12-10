TEM Control is a remote control of TEM since remote access to the microscope itself is often not available to the end user. Simple operations in this includes some sanity check before they are sent to the scope.

-   Required bindings*

TEMControllerNodeAlias- (ChangePresetEvent) -> PresetsManagerNode
PresetsManagerNode - (PresetChangedEvent) -> TEMControllerNodeAlias

-   Settings*

None

## Operation

### To make the node aware of what instrument it is connected to, send a preset to scope and then click the refresh tool.

![](images/tem_controller_tools.png)

### Available Controls:

-   preset change
-   autoloader grid exchange for Arctica/Krios/Glacios
-   aperture insertion/retraction
-   column valve opening/closing
-   general puase and resume
-   reset stage position in axes xy, z, alpha

### Available Information:

-   Selective vacuum gauge values
