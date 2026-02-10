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
 * Jeonggwan Scenario with DRT (Demand Responsive Transport)
 * Extends the base scenario with stopbased DRT service
 */
@CommandLine.Command(header = ":: Jeonggwan DRT Scenario ::", mixinStandardHelpOptions = true, showDefaultValues = true)
public class RunJeonggwanDrt extends MATSimApplication {

	@CommandLine.Option(names = "--drt-config", defaultValue = "input/jeonggwan-drt-config.xml",
		description = "Path to DRT configuration file")
	private String drtConfigPath;

	public RunJeonggwanDrt() {
		super("input/jeonggwan-config.xml");
	}

	public static void main(String[] args) {
		if (args.length == 0) {
			args = new String[]{"run"};
		}
		MATSimApplication.run(RunJeonggwanDrt.class, args);
	}

	@Override
	protected Config prepareConfig(Config config) {
		System.out.println("### Configuring Jeonggwan DRT Scenario ###");

		// Explicitly add DRT and DVRP config groups BEFORE loading the file
		// This ensures they are parsed as the correct classes, not generic ConfigGroups
		ConfigUtils.addOrGetModule(config, MultiModeDrtConfigGroup.class);
		ConfigUtils.addOrGetModule(config, DvrpConfigGroup.class);

		// Load DRT config
		ConfigUtils.loadConfig(config, drtConfigPath);

		// Modify output directory for DRT run
		config.controller().setOutputDirectory(config.controller().getOutputDirectory() + "-drt");
		config.controller().setRunId(config.controller().getRunId() + "-drt");

		// DRT requires this setting
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

		// Configure DRT scoring (copy from PT)
		MultiModeDrtConfigGroup multiModeDrtCfg = MultiModeDrtConfigGroup.get(config);
		DrtConfigs.adjustMultiModeDrtConfig(multiModeDrtCfg, config.scoring(), config.routing());

		// Get scoring params from PT
		org.matsim.core.config.groups.ScoringConfigGroup.ModeParams ptParams = 
			config.scoring().getModes().get(TransportMode.pt);

		// Add DRT to mode choice
		Set<String> modes = new HashSet<>();
		modes.add("car");
		modes.add("pt");
		modes.add("walk");
		modes.add("drt");  // Add DRT mode
		config.subtourModeChoice().setModes(modes.toArray(new String[0]));
		config.subtourModeChoice().setChainBasedModes(new String[]{"car"});

		// Configure DRT scoring params (same as PT)
		for (DrtConfigGroup drtCfg : multiModeDrtCfg.getModalElements()) {
			org.matsim.core.config.groups.ScoringConfigGroup.ModeParams modeParams = 
				new org.matsim.core.config.groups.ScoringConfigGroup.ModeParams(drtCfg.getMode());
			
			if (ptParams != null) {
				modeParams.setConstant(ptParams.getConstant());
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
		// This ensures that when DRT trips are created, they use DrtRoute instead of GenericRouteImpl
		scenario.getPopulation().getFactory().getRouteFactories().setRouteFactory(
			org.matsim.contrib.drt.routing.DrtRoute.class,
			new org.matsim.contrib.drt.routing.DrtRouteFactory()
		);
	}

	@Override
	protected void prepareControler(Controler controler) {
		System.out.println("### Adding DRT modules to controler ###");

		// Add DVRP and DRT modules
		controler.addOverridingModule(new DvrpModule());
		controler.addOverridingModule(new MultiModeDrtModule());

		// Configure QSim components for DRT
		Config config = controler.getConfig();
		MultiModeDrtConfigGroup multiModeDrtCfg = MultiModeDrtConfigGroup.get(config);
		
		controler.configureQSimComponents(
			DvrpQSimComponents.activateAllModes(multiModeDrtCfg)
		);
	}
}
