DE12 and DE Survey camera are retract/extend together, with the survey camera at off-axis. Therefore zplane should be set at the same value
For example,

    [camera1]
    class: de.DE12
    zplane: 50

    [camera2]
    class: de.DESurvey
    zplane: 50
