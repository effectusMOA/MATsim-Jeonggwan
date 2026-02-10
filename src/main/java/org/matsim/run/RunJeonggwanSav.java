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
import org.matsim.core.controler.Controler;
import picocli.CommandLine;

import java.util.HashSet;
import java.util.Set;

/**
 * Jeonggwan Scenario with SAV (Shared Autonomous Vehicle)
 * Uses door-to-door DRT service (no predefined stops)
 * SAV differs from DRT: no stops, shorter wait time, fewer vehicles
 */
@CommandLine.Command(header = ":: Jeonggwan SAV Scenario ::", mixinStandardHelpOptions = true, showDefaultValues = true)
public class RunJeonggwanSav extends MATSimApplication {

	@CommandLine.Option(names = "--sav-config", defaultValue = "input/jeonggwan-sav-config.xml",
		description = "Path to SAV configuration file")
	private String savConfigPath;

	public RunJeonggwanSav() {
		super("input/jeonggwan-config.xml");
	}

	public static void main(String[] args) {
		if (args.length == 0) {
			args = new String[]{"run"};
		}
		MATSimApplication.run(RunJeonggwanSav.class, args);
	}

	@Override
	protected Config prepareConfig(Config config) {
		System.out.println("### Configuring Jeonggwan SAV (Shared Autonomous Vehicle) Scenario ###");

		// Explicitly add DRT and DVRP config groups BEFORE loading the file
		ConfigUtils.addOrGetModule(config, MultiModeDrtConfigGroup.class);
		ConfigUtils.addOrGetModule(config, DvrpConfigGroup.class);

		// Load SAV config
		ConfigUtils.loadConfig(config, savConfigPath);

		// Modify output directory for SAV run
		config.controller().setOutputDirectory(config.controller().getOutputDirectory() + "-sav");
		config.controller().setRunId(config.controller().getRunId() + "-sav");

		// DRT/SAV requires this setting
		config.qsim().setSimStarttimeInterpretation(
			org.matsim.core.config.groups.QSimConfigGroup.StarttimeInterpretation.onlyUseStarttime);

		// Adjust BestScore weight
		for (org.matsim.core.config.groups.ReplanningConfigGroup.StrategySettings settings : 
			config.replanning().getStrategySettings()) {
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

		// Configure SAV scoring
		MultiModeDrtConfigGroup multiModeDrtCfg = MultiModeDrtConfigGroup.get(config);
		DrtConfigs.adjustMultiModeDrtConfig(multiModeDrtCfg, config.scoring(), config.routing());

		// Get scoring params from PT
		org.matsim.core.config.groups.ScoringConfigGroup.ModeParams ptParams = 
			config.scoring().getModes().get(TransportMode.pt);

		// Add SAV to mode choice
		Set<String> modes = new HashSet<>();
		modes.add("car");
		modes.add("pt");
		modes.add("walk");
		modes.add("sav");  // Add SAV mode
		config.subtourModeChoice().setModes(modes.toArray(new String[0]));
		config.subtourModeChoice().setChainBasedModes(new String[]{"car"});

		// Configure SAV scoring params (slightly better than PT - autonomous = more comfortable)
		for (DrtConfigGroup drtCfg : multiModeDrtCfg.getModalElements()) {
			org.matsim.core.config.groups.ScoringConfigGroup.ModeParams modeParams = 
				new org.matsim.core.config.groups.ScoringConfigGroup.ModeParams(drtCfg.getMode());
			
			if (ptParams != null) {
				modeParams.setConstant(ptParams.getConstant() + 0.5);  // Slightly more attractive than PT
				modeParams.setMarginalUtilityOfDistance(ptParams.getMarginalUtilityOfDistance());
				modeParams.setMarginalUtilityOfTraveling(ptParams.getMarginalUtilityOfTraveling());
				modeParams.setDailyUtilityConstant(ptParams.getDailyUtilityConstant());
				modeParams.setMonetaryDistanceRate(ptParams.getMonetaryDistanceRate());
				modeParams.setDailyMonetaryConstant(ptParams.getDailyMonetaryConstant());
			}
			config.scoring().addModeParams(modeParams);
		}

		return config;
	}

	@Override
	protected void prepareScenario(Scenario scenario) {
		// Register DRT route factory to avoid ClassCastException
		// SAV uses the same route class as DRT
		scenario.getPopulation().getFactory().getRouteFactories().setRouteFactory(
			org.matsim.contrib.drt.routing.DrtRoute.class,
			new org.matsim.contrib.drt.routing.DrtRouteFactory()
		);
	}

	@Override
	protected void prepareControler(Controler controler) {
		System.out.println("### Adding SAV (door-to-door) modules to controler ###");

		// Add DVRP and DRT modules (SAV uses same modules)
		controler.addOverridingModule(new DvrpModule());
		controler.addOverridingModule(new MultiModeDrtModule());

		// Configure QSim components for SAV
		Config config = controler.getConfig();
		MultiModeDrtConfigGroup multiModeDrtCfg = MultiModeDrtConfigGroup.get(config);
		
		controler.configureQSimComponents(
			DvrpQSimComponents.activateAllModes(multiModeDrtCfg)
		);
	}
}
