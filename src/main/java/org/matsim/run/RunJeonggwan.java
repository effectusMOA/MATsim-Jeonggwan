package org.matsim.run;

import org.matsim.application.MATSimApplication;
import org.matsim.core.config.Config;
import org.matsim.analysis.QsimTimingModule;
import org.matsim.analysis.personMoney.PersonMoneyEventsAnalysisModule;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.Controler;
import org.matsim.run.analysis.SimpleEmissionAnalysisModule;
import org.matsim.run.analysis.JeonggwanDashboardProvider;
import org.matsim.simwrapper.DashboardProvider;
import org.matsim.simwrapper.SimWrapperConfigGroup;
import org.matsim.simwrapper.SimWrapperModule;
import org.matsim.core.controler.AbstractModule;
import picocli.CommandLine;

/**
 * Jeonggwan Scenario - Base Version (PT + Car + Walk only)
 * 
 * Uses v6 configuration with:
 * - Network: jeonggwan-network-expanded.xml
 * - Plans: jeonggwan-plans-v4.xml
 * - Transit: regional-transit-schedule.xml (KTDB data)
 * - Transit Router: Optimized for 3+ transfers (maxTransfers=5)
 * 
 * This is the baseline scenario WITHOUT DRT/SAV for comparison.
 */
@CommandLine.Command(header = ":: Jeonggwan Scenario (PT+Car+Walk) ::", mixinStandardHelpOptions = true, showDefaultValues = true)
public class RunJeonggwan extends MATSimApplication {

	public RunJeonggwan() {
		// Use v6-baseline config (no DRT/SAV) with regional transit network
		super("input/jeonggwan-config-v6-baseline.xml");
	}


	public static void main(String[] args) {
		if (args.length == 0) {
			args = new String[]{"run"};
		}
		MATSimApplication.run(RunJeonggwan.class, args);
	}

	@Override
	protected Config prepareConfig(Config config) {
		ConfigUtils.addOrGetModule(config, SimWrapperConfigGroup.class);
		System.out.println("### Jeonggwan v6 Baseline Scenario (PT + Car + Walk) ###");
		System.out.println("### Network: " + config.network().getInputFile() + " ###");
		System.out.println("### Plans: " + config.plans().getInputFile() + " ###");
		System.out.println("### Transit: " + config.transit().getTransitScheduleFile() + " ###");
		
		// Update output directory to distinguish from multimode
		// Explicitly set output directory for v8
		config.controller().setOutputDirectory("output/jeonggwan-v8");
		config.controller().setLastIteration(100);
		
		// Adjust BestScore weight to 0.7 to make room for SubtourModeChoice (Total 1.0)
		for (org.matsim.core.config.groups.ReplanningConfigGroup.StrategySettings settings : config.replanning().getStrategySettings()) {
			if (settings.getStrategyName().equals("BestScore")) {
				settings.setWeight(0.7);
			}
		}

		// Enable SubtourModeChoice
		config.replanning().addStrategySettings(
			new org.matsim.core.config.groups.ReplanningConfigGroup.StrategySettings()
				.setStrategyName("SubtourModeChoice")
				.setWeight(0.10)
		);

		// Configure SubtourModeChoice - Only car, pt, walk (NO DRT/SAV)
		config.subtourModeChoice().setModes(new String[]{"car", "pt", "walk"});
		config.subtourModeChoice().setChainBasedModes(new String[]{"car"});
		
		System.out.println("### SubtourModeChoice modes: car, pt, walk ###");
		System.out.println("### TransitRouter: maxTransfers=5 (set in config XML) ###");

		return config;
	}

	@Override
	protected void prepareControler(Controler controler) {
		controler.addOverridingModule(new SimWrapperModule());
		controler.addOverridingModule(new QsimTimingModule());
		controler.addOverridingModule(new PersonMoneyEventsAnalysisModule());
		controler.addOverridingModule(new SimpleEmissionAnalysisModule());
		controler.addOverridingModule(new AbstractModule() {
			@Override
			public void install() {
				bind(DashboardProvider.class).to(JeonggwanDashboardProvider.class);
			}
		});

		// No additional modules needed for baseline scenario
		// PT is handled by standard MATSim transit routing
		System.out.println("### Baseline scenario - No DRT/SAV modules ###");
	}
}
