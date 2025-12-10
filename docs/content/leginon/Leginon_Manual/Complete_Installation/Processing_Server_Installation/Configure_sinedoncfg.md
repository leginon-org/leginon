> **Note:** See external reference `appion:Configure sinedon.cfg shared`

* Add database configuration if you intend to use grid-inserting robot. The Robot2 module uses the database to communicate to the robot. Applications that carries the name "Robot" requires this to be set. In general, using the same database as the general leginon database is fine.

          [robot2]
          db: leginondb

[< Configure leginon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg) | [Create Simulated instruments.cfg >](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Create_simulated_instrumentscfg)
