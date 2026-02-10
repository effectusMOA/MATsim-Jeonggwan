package org.matsim.run;

import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.application.MATSimApplication;
import org.matsim.contrib.drt.run.DrtConfigGroup;
import org.matsim.contrib.drt.run.DrtConfigs;
import org.matsim.contrib.drt.run.MultiModeDrtConfigGroup;
import org.matsim.contrib.drt.run.MultiModeDrtModule;
import org.matsim.contrib.dvrp.run.DvrpConfigGroup;
import org.matsim.contrib.dvrp.run.DvrpModule;
import org.matsim.contrib.dvrp.run.DvrpQSimComponents;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.analysis.QsimTimingModule;
import org.matsim.analysis.personMoney.PersonMoneyEventsAnalysisModule;
import org.matsim.core.controler.Controler;
import org.matsim.run.analysis.SimpleEmissionAnalysisModule;
import org.matsim.run.analysis.JeonggwanDashboardProvider;
import org.matsim.simwrapper.DashboardProvider;
import org.matsim.core.controler.AbstractModule;
import org.matsim.simwrapper.SimWrapperConfigGroup;
import org.matsim.simwrapper.SimWrapperModule;
import picocli.CommandLine;

import java.util.HashSet;
import java.util.Set;

/**
 * Jeonggwan Scenario with Multi-Mode: DRT + SAV
 * 
 * Uses v6 configuration with:
 * - Network: jeonggwan-network-expanded.xml
 * - Plans: jeonggwan-plans-v4.xml
 * - Transit: regional-transit-schedule.xml (KTDB data)
 * - Transit Router: Optimized for 3+ transfers (maxTransfers=5)
 * 
 * DRT: Stop-based, 5 vehicles, 20 seats (minibus style)
 * SAV: Door-to-door, 10 vehicles, 4 seats
 */
@CommandLine.Command(header = ":: Jeonggwan Multi-Mode (DRT+SAV) Scenario ::", mixinStandardHelpOptions = true, showDefaultValues = true)
public class RunJeonggwanMultiMode extends MATSimApplication {

	@CommandLine.Option(names = "--multimode-config", defaultValue = "input/jeonggwan-multimode-config.xml",
		description = "Path to multi-mode configuration file")
	private String multiModeConfigPath;

	public RunJeonggwanMultiMode() {
		// Use v6 config with regional transit network and optimized transitRouter
		super("input/jeonggwan-config-v6.xml");
	}


	public static void main(String[] args) {
		if (args.length == 0) {
			args = new String[]{"run"};
		}
		MATSimApplication.run(RunJeonggwanMultiMode.class, args);
	}

	@Override
	protected Config prepareConfig(Config config) {
		ConfigUtils.addOrGetModule(config, SimWrapperConfigGroup.class);
		System.out.println("### Configuring Jeonggwan Multi-Mode (DRT + SAV) Scenario ###");

		// Clear existing MultiModeDrt module to prevent duplicates if inadvertently loaded
		config.removeModule("multiModeDrt");
		
		// Register DRT and DVRP config groups
		ConfigUtils.addOrGetModule(config, MultiModeDrtConfigGroup.class);
		ConfigUtils.addOrGetModule(config, DvrpConfigGroup.class);

		// Load multi-mode config (contains both DRT and SAV)
		ConfigUtils.loadConfig(config, multiModeConfigPath);

		// Modify output directory for v8
		config.controller().setOutputDirectory("output/jeonggwan-v8-multimode");
		config.controller().setRunId("jeonggwan-v8-multimode");
		config.controller().setLastIteration(100);

		// Required for DRT/SAV
		config.qsim().setSimStarttimeInterpretation(
			org.matsim.core.config.groups.QSimConfigGroup.StarttimeInterpretation.onlyUseStarttime);

		// Strategy settings are now handled in jeonggwan-config.xml
		// SubtourModeChoice parameters are also handled in jeonggwan-config.xml

		// Configure scoring
		MultiModeDrtConfigGroup multiModeDrtCfg = MultiModeDrtConfigGroup.get(config);
		DrtConfigs.adjustMultiModeDrtConfig(multiModeDrtCfg, config.scoring(), config.routing());
		
		// Add valid modes for SubtourModeChoice from config if needed validation? 
		// Actually, params like 'modes', 'chainBasedModes' are already loaded from XML.
		// We just print a confirmation.
		System.out.println("### Car availability constraint enabled in Config XML ###");

		// Configure scoring for each DRT mode based on academic framework
		// Reference: Krueger et al. (2016), Alonso-Mora et al. (2017)
		// Hierarchy: Car(0) > SAV(-0.7) > DRT(-1.5) > PT(-2.5)
		// Note: Fare is handled by drtfare module in jeonggwan-multimode-config.xml
		for (DrtConfigGroup drtCfg : multiModeDrtCfg.getModalElements()) {
			org.matsim.core.config.groups.ScoringConfigGroup.ModeParams modeParams = 
				new org.matsim.core.config.groups.ScoringConfigGroup.ModeParams(drtCfg.getMode());
			
			String mode = drtCfg.getMode();
			
			if (mode.equals("sav")) {
				// SAV: ASC = -0.7 (door-to-door but waiting uncertainty, sharing disutility)
				modeParams.setConstant(-0.7);
				System.out.println("### SAV ASC = -0.7 (Door-to-door, but waiting/sharing penalty) ###");
			} else if (mode.equals("drt")) {
				// DRT: ASC = -1.5 (stop-based, access walk, detour possibility)
				modeParams.setConstant(-1.5);
				System.out.println("### DRT ASC = -1.5 (Stop-based, access walk required) ###");
			}
			
			// Common parameters for DRT/SAV
			// dailyMonetaryConstant = 0 (fare handled by drtfare module)
			modeParams.setDailyMonetaryConstant(0.0);
			modeParams.setMarginalUtilityOfDistance(0.0);
			modeParams.setMarginalUtilityOfTraveling(0.0);
			modeParams.setDailyUtilityConstant(0.0);
			modeParams.setMonetaryDistanceRate(0.0);
			
			config.scoring().addModeParams(modeParams);
			System.out.println("Added mode: " + mode + " with constant=" + modeParams.getConstant());
		}

		return config;
	}

	@Override
	protected void prepareScenario(Scenario scenario) {
		// Register DRT route factory for both modes
		scenario.getPopulation().getFactory().getRouteFactories().setRouteFactory(
			org.matsim.contrib.drt.routing.DrtRoute.class,
			new org.matsim.contrib.drt.routing.DrtRouteFactory()
		);
	}

	@Override
	protected void prepareControler(Controler controler) {
		controler.addOverridingModule(new SimWrapperModule());
		controler.addOverridingModule(new QsimTimingModule());
		controler.addOverridingModule(new PersonMoneyEventsAnalysisModule());
		controler.addOverridingModule(new SimpleEmissionAnalysisModule());
		// controler.addOverridingModule(new AbstractModule() {
		// 	@Override
		// 	public void install() {
		// 		bind(DashboardProvider.class).to(JeonggwanDashboardProvider.class);
		// 	}
		// });
		// Use default SimWrapper dashboards for MultiMode to ensure DRT/SAV visualization coverage
		System.out.println("### Adding Multi-Mode (DRT + SAV) modules to controler ###");

		// Add DVRP and DRT modules
		controler.addOverridingModule(new DvrpModule());
		controler.addOverridingModule(new MultiModeDrtModule());

		// Configure QSim for all DRT modes
		Config config = controler.getConfig();
		MultiModeDrtConfigGroup multiModeDrtCfg = MultiModeDrtConfigGroup.get(config);
		
		controler.configureQSimComponents(
			DvrpQSimComponents.activateAllModes(multiModeDrtCfg)
		);
	}
}
