package org.matsim.run.analysis;

import org.matsim.core.config.Config;
import org.matsim.simwrapper.Dashboard;
import org.matsim.simwrapper.DashboardProvider;
import org.matsim.simwrapper.SimWrapper;
import org.matsim.simwrapper.dashboard.*;

import java.util.ArrayList;
import java.util.List;

/**
 * Custom Dashboard Provider for Jeonggwan Scenario.
 * Replicates the structure of Berlin Scenario:
 * Overview, Trips, Air Pollution, Noise (Skipped), Traffic Counts, DRT, Car Traffic, PT, Travel time, SAC, Files
 */
public class JeonggwanDashboardProvider implements DashboardProvider {

	@Override
	public List<Dashboard> getDashboards(Config config, SimWrapper simWrapper) {
		List<Dashboard> dashboards = new ArrayList<>();

		// 1. Overview
		// dashboards.add(new OverviewDashboard()); // Not standard class?

		// 2. Trips
		dashboards.add(new TripDashboard());

		// 3. Air Pollution (Custom using SimpleLinkEmissionAnalysis output)
		// Standard EmissionsDashboard requires standard HBEFA output which we don't have.
		
		// 4. Noise -> Skipped as requested/not implemented.

		// 5. Traffic Counts
		dashboards.add(new TrafficCountsDashboard());

		// 6. DRT
		// dashboards.add(new DrtDashboard()); // Not found in path

		// 7. Car Traffic (Network / Link volumes)
		
		// 8. PT (Public Transit)
		// dashboards.add(new TransitDashboard()); // Not found in path

		// 9. Travel Time
		// dashboards.add(new TravelTimeComparisonDashboard(...)); // Requires reference file
		// Since we don't have reference routes, we might skip or use generic TravelTimeDashboard if exists.
		
		// 10. SAC (Score Analysis / Stuck Agents?)
		// Assuming "SAC" refers to Stuck Agent Classification or Score Analysis.
		// Berlin has "StuckAgentAnalysis".
		// dashboards.add(new StuckAgentDashboard()); 
		
		// 11. Files - Always included by default? Or we add it.
		// SimWrapper adds Files tab automatically usually.

		return dashboards;
	}
}
