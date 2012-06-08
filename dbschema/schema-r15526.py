#!/usr/bin/env python
import schemabase
import leginon.leginondata
import leginon.projectdata

class SchemaUpdate15526(schemabase.SchemaUpdate):
    '''
    This will add a new table to the Project database for keeping track of system statistics: dataStatusReport
    '''

    def upgradeProjectDB(self):
    	tablename = "dataStatusReport"
    	
        intNotNull = 'int(11) NOT NULL DEFAULT 0' 
        bigIntNotNull = 'bigint(20) NOT NULL DEFAULT 0' 
        timestampZeroDefault = 'timestamp NOT NULL default "0000-00-00-00:00:00"'
    	
    	# it is important that the fields are added in this exact order
        columns = [ ("appion_project", intNotNull), 
    			   ("processed_session", intNotNull),
    			   ("processed_run", intNotNull),
    			   ("last_exp_runtime", timestampZeroDefault),
    			   ("ace_run", intNotNull),
    			   ("ace2_run", intNotNull),
    			   ("ctfind_run", intNotNull),
    			   ("ace_processed_image", intNotNull),
    			   ("particle_selection", intNotNull),
    			   ("dog_picker", intNotNull),
    			   ("manual_picker", intNotNull),
    			   ("tilt_picker", intNotNull),
    			   ("template_picker", intNotNull),
    			   ("selected_particle", intNotNull),
    			   ("classification", intNotNull),
    			   ("classes", intNotNull),
    			   ("classified_particles", bigIntNotNull),
    			   ("RCT_Models", intNotNull),
    			   ("tomogram", intNotNull),
    			   ("stack", intNotNull),
    			   ("stack_particle", bigIntNotNull),
    			   ("3D_recon", intNotNull),
    			   ("recon_iteration", intNotNull),
    			   ("classified_particle", bigIntNotNull),
    			   ("template", intNotNull),
    			   ("initial_model", intNotNull),
                   ("first_exp_runtime", timestampZeroDefault) ]
    		
        # if the table already exists, do not add it
        if not self.project_dbupgrade.tableExists( tablename ): 
            # add the new table to the database 
            self.project_dbupgrade.createTable( tablename )
			
            # add the new columns to the new table
            for column, columndefine in columns:
                self.project_dbupgrade.addColumn( tablename, column, columndefine )

if __name__ == "__main__":
	update = SchemaUpdate15526()
	update.setRequiredUpgrade('project')
	update.run()

