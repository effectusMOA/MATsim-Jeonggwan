package org.matsim.run;

import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * Run Jeonggwan simulation with Excel-based population data.
 * 
 * Population: 53,414 agents from 정관_test.xlsx
 * Network: Expanded MOCT network (175,698 nodes, 248,400 links)
 * Mode: All trips as car (initial)
 */
public class RunJeonggwanExcel {
    
    public static void main(String[] args) {
        String configPath = args.length > 0 ? args[0] : "input/jeonggwan-config-excel.xml";
        
        Config config = ConfigUtils.loadConfig(configPath);
        
        // Overwrite output
        config.controller().setOverwriteFileSetting(
            OutputDirectoryHierarchy.OverwriteFileSetting.deleteDirectoryIfExists
        );
        
        // Load scenario
        Scenario scenario = ScenarioUtils.loadScenario(config);
        
        // Create controler
        Controler controler = new Controler(scenario);
        
        // Run simulation
        controler.run();
    }
}
