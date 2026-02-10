package org.matsim.run.analysis;

import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.events.LinkLeaveEvent;
import org.matsim.api.core.v01.events.VehicleEntersTrafficEvent;
import org.matsim.api.core.v01.events.handler.LinkLeaveEventHandler;
import org.matsim.api.core.v01.events.handler.VehicleEntersTrafficEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.utils.io.IOUtils;
import org.matsim.vehicles.Vehicle;
import com.google.inject.Inject;

import java.io.BufferedWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Calculates emissions based on simple average factors per km.
 * Factors provided:
 * Car: 128.8 g/km
 * Bus: 869.8 g/km
 * DRT: 210.0 g/km
 * SAV: 43.7 g/km
 */
public class SimpleLinkEmissionAnalysis implements VehicleEntersTrafficEventHandler, LinkLeaveEventHandler {

	private final Network network;
	private final Map<Id<Vehicle>, String> vehicleModes = new ConcurrentHashMap<>();
	private final Map<Id<Link>, Double> linkEmissions = new ConcurrentHashMap<>();

	// Emission factors in g/km
	// Converted to g/m for easier calculation: g/km / 1000
	private final Map<String, Double> emissionFactors = new HashMap<>();

	@Inject
	public SimpleLinkEmissionAnalysis(Network network) {
		this.network = network;
		// Initialize factors (g/m)
		emissionFactors.put("car", 128.8 / 1000.0);
		emissionFactors.put("bus", 869.8 / 1000.0);
		emissionFactors.put("pt", 869.8 / 1000.0); // Assume pt is bus
		emissionFactors.put("drt", 210.0 / 1000.0);
		emissionFactors.put("sav", 43.7 / 1000.0); // Electric SAV
		// Add aliases or defaults
		emissionFactors.put("taxi", 128.8 / 1000.0); // Treat taxi as car
		emissionFactors.put("truck", 0.0); // No data provided, maybe assume high? or 0.
		emissionFactors.put("freight", 0.0);
	}

	@Override
	public void handleEvent(VehicleEntersTrafficEvent event) {
		vehicleModes.put(event.getVehicleId(), event.getNetworkMode());
	}

	@Override
	public void handleEvent(LinkLeaveEvent event) {
		String mode = vehicleModes.get(event.getVehicleId());
		if (mode == null) return;
		
		// If mode matches one of our targets (or contains string)
		// Basic exact match first
		Double factor = emissionFactors.get(mode);
		
		// Fallback logic if exact string not found
		if (factor == null) {
			if (mode.contains("car")) factor = emissionFactors.get("car");
			else if (mode.contains("bus")) factor = emissionFactors.get("bus");
			else if (mode.contains("drt")) factor = emissionFactors.get("drt");
			else return; // Ignore walk, bike, etc.
		}

		Link link = network.getLinks().get(event.getLinkId());
		if (link == null) return;

		double length = link.getLength(); // meters
		double emissions = length * factor; // g

		linkEmissions.merge(event.getLinkId(), emissions, Double::sum);
	}

	public void writeResults(String outputFile) {
		try (BufferedWriter writer = IOUtils.getBufferedWriter(outputFile)) {
			writer.write("linkId;fraction;emissions_total_g;emissions_per_meter_g_m\n");
			
			for (Map.Entry<Id<Link>, Double> entry : linkEmissions.entrySet()) {
				Id<Link> linkId = entry.getKey();
				double totalEmissions = entry.getValue();
				Link link = network.getLinks().get(linkId);
				double length = (link != null) ? link.getLength() : 1.0;
				double perMeter = totalEmissions / length;

				// SimWrapper often expects "value" or specific columns, but standard CSV is fine.
				// "fraction" is just a dummy column often used in SimWrapper link visualizations if checking capacity, 
				// but here we just output raw data.
				
				writer.write(linkId.toString() + ";" + 
						     String.format("%.4f", perMeter/100.0) + ";" + // scaled for visualization? No, just raw.
						     String.format("%.2f", totalEmissions) + ";" + 
						     String.format("%.4f", perMeter) + "\n");
			}
		} catch (IOException e) {
			throw new RuntimeException("Could not write emission results", e);
		}
	}
	
	@Override
	public void reset(int iteration) {
		vehicleModes.clear();
		linkEmissions.clear();
	}
}
