package org.matsim.run.analysis;

import com.google.inject.Inject;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.controler.AbstractModule;
import org.matsim.core.controler.events.ShutdownEvent;
import org.matsim.core.controler.listener.ShutdownListener;
import org.matsim.core.controler.OutputDirectoryHierarchy;

import javax.inject.Provider;

public class SimpleEmissionAnalysisModule extends AbstractModule {
	@Override
	public void install() {
		addControlerListenerBinding().to(EmissionWriteListener.class);
		bind(SimpleLinkEmissionAnalysis.class).asEagerSingleton();
		addEventHandlerBinding().to(SimpleLinkEmissionAnalysis.class);
	}

	private static class EmissionWriteListener implements ShutdownListener {
		@Inject
		private SimpleLinkEmissionAnalysis analysis;
		@Inject
		private OutputDirectoryHierarchy controlerIO;

		@Override
		public void notifyShutdown(ShutdownEvent event) {
			String filename = controlerIO.getOutputFilename("analysis/emissions_per_link.csv");
			// Create directory if not exists? OutputDirectoryHierarchy handles path but maybe not mkdirs for 'analysis'
			// Usually Controler creates root output. 'analysis/' might need creation if it's a subfolder.
			// But getOutputFilename usually returns full path.
			
			// We'll trust SimWrapper or user to look for it. Best to put it in root or analysis folder.
			// SimWrapper usually looks in 'analysis'.
			// We need to ensure the folder exists.
			
			try {
				java.nio.file.Files.createDirectories(java.nio.file.Paths.get(filename).getParent());
			} catch (java.io.IOException e) {
				e.printStackTrace();
			}
			
			analysis.writeResults(filename);
		}
	}
}
