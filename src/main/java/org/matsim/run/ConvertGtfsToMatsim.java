package org.matsim.run;

import org.matsim.api.core.v01.Scenario;
//import org.matsim.contrib.gtfs.GtfsConverter;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.utils.geometry.CoordinateTransformation;
import org.matsim.core.utils.geometry.transformations.TransformationFactory;

import java.time.LocalDate;

public class ConvertGtfsToMatsim {

    public static void main(String[] args) {
        System.out.println("Conversion logic commented out for debugging.");
        /*
        String gtfsFolder = "input/jeonggwan-gtfs";
        String outputSchedule = "input/jeonggwan-transit-schedule.xml";
        String outputVehicles = "input/jeonggwan-transit-vehicles.xml";
        
        // Coordinate Transformation: WGS84 (GTFS) -> EPSG:5179 (Jeonggwan)
        CoordinateTransformation transform = TransformationFactory.getCoordinateTransformation(
                "EPSG:4326", "EPSG:5179");

        // Date to extract: Pick a weekday in March 2023 (e.g., 2023-03-15)
        LocalDate date = LocalDate.of(2023, 3, 15);

        Scenario scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
        
        GtfsConverter converter = GtfsConverter.newBuilder()
                .setScenario(scenario)
                .setTransform(transform)
                .setDate(date)
                .setFeed(gtfsFolder)
                .setMergeStops(true)
                .build();

        converter.convert();
        
        // Save
        new org.matsim.pt.transitSchedule.api.TransitScheduleWriter(scenario.getTransitSchedule()).writeFile(outputSchedule);
        new org.matsim.vehicles.VehicleWriterV1(scenario.getTransitVehicles()).writeFile(outputVehicles);
        
        System.out.println("Conversion completed!");
        */
    }
}
