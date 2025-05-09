Terminology
===========

.. glossary::

    Aliasing  
        A signal distortion that occurs when a signal is sampled at too low a rate to capture its frequency content accurately. Frequencies higher than the Nyquist frequency appear as lower-frequency artifacts in the data, potentially causing misleading results in spike or oscillation detection.

    Amplitude  
        The strength (height) of a signal measured in millivolts (mV).

    Artifact  
        Noise or signal distortion in recordings that does not represent true biological activity.

    Artifact rejection  
        The process of removing or ignoring non-biological noise (e.g., mechanical vibration, electrical interference) during analysis.

    Baseline  
        The level of electrical activity recorded when the tissue is in a resting or non-seizure state. Used as a reference for detecting discharges and SLEs.

    Burst  
        A cluster of spikes that occur close together in time.

    Burst detection  
        A method of identifying clusters of rapid spikes that may indicate heightened neural activity, sometimes preceding a seizure.

    Channel  
        A data stream corresponding to a single electrode's recording. In the GUI, each electrode is associated with one channel, which carries the digitized signal data from that electrode in the MEA.

    DBSCAN algorithm  
        Density-Based Spatial Clustering of Applications with Noise — a machine learning algorithm that groups data points into clusters based on their density. In this GUI, DBSCAN may be used to identify spatial clusters of electrodes involved in a discharge or seizure event.

    Discharge  
        A brief period of increased electrical activity recorded from neural tissue. In this GUI, a discharge typically refers to a localized burst of electrical signals detected on one or more electrodes. Discharges may represent isolated neuronal events or parts of larger seizure-like episodes (SLEs). The GUI analyzes discharges to detect patterns of abnormal neural activity, such as seizures or excessive synchrony between neurons.

    Discharge event  
        A brief burst of electrical activity detected in a localized region of the brain slice. In the context of this GUI, a discharge event is typically detected using amplitude or frequency thresholds on Local Field Potential (LFP) signals.

    Discharge propagation  
        The spread of a discharge event across the electrode array over time. It reflects the spatial and temporal recruitment of neural populations and is visualized using false color maps and LFP traces from multiple channels.

    Electrode  
        A physical recording site on the Multi-Electrode Array (MEA) that picks up electrical signals from neural tissue. Each electrode captures local voltage changes from nearby neurons.

    Frames  
        A single time point in the visualization or video output of the GUI, corresponding to a fixed time interval (e.g., 1 ms). Multiple frames make up a time-resolved representation of activity across the MEA.

    GUI (Graphical User Interface)  
        The visual interface that allows users to interact with the software without using command-line commands.

    Local Field Potential (LFP)  
        Local Field Potential (LFP) signals showing low-frequency voltage changes from groups of neurons, useful for spotting discharges and seizure-like events.

    Metadata panel  
        A summary display that shows key information about the recording file, such as the total duration, number of electrodes, sampling rate, and processing status. Useful for quickly verifying file properties before analysis.

    Multi-Electrode Array (MEA)  
        A platform with many electrodes that record electrical signals from biological tissues like brain slices.

    Nyquist frequency  
        The highest frequency that can be reliably detected in a sampled signal, equal to half the sampling rate. For example, if MEA data is sampled at 10 kHz, the Nyquist frequency is 5 kHz. Frequencies above this cause aliasing and are not accurately represented.

    Raster Plot  
        A graphical representation showing the timing of spikes (action potentials) recorded across multiple electrodes. Each row represents one electrode, and each tick mark represents a detected spike at a specific time. Useful for visualizing patterns of neuronal activity across the array.

    Seizure-Like Events (SLEs)  
        A discrete burst of abnormal electrical activity in brain slice recordings that resembles an epileptic seizure but is typically shorter and less severe than status epilepticus (SE). SLEs may arise spontaneously in ex vivo preparations and are often used as experimental models of seizure behavior.

        In this GUI, SLEs are automatically detected using threshold-based criteria and appear in visualizations such as raster plots and LFP traces. Spike events associated with SLEs are marked in blue in the raster plot. You can toggle color modes in the trace plot to see SLE activity in blue to visually differentiate SLE activity across selected channels.

    Spectrogram  
        A visual representation of how the frequency content of a signal changes over time. In neuroscience, spectrograms are often used to detect shifts in power across frequency bands during seizure events or other dynamic network activity.

    Spike  
        A rapid increase in voltage that often corresponds to neuronal firing.

    Status Epilepticus (SE)  
        A prolonged seizure state characterized by continuous or rapidly repeating seizure activity, typically lasting more than 5 minutes without recovery between events. Medically, SE is considered a neurological emergency that can lead to long-term brain damage, neuronal death, or life-threatening complications if not treated promptly.

        In this GUI, SE events are automatically detected based on defined thresholds and visualized alongside other seizure-like activity. They are marked with orange spike indicators in the raster plot. You can also toggle the color mode in the trace plot to see SE events in yellow, making it easier to distinguish SE from other activity across multiple views.

    Synchronous activity  
        When many electrodes detect similar signals at nearly the same time, indicating widespread neural coordination (often seen in seizures).

    Peak  
        A local maximum in the Local Field Potential (LFP) signal, often representing a spike or a feature of interest in neural activity. In this GUI, peaks are detected using configurable thresholds (e.g., amplitude, distance between peaks) and are used as the basis for spike and burst detection during analysis.

    Peak detection threshold  
        The minimum amplitude a peak must reach to be considered valid during spike or burst detection. This threshold helps distinguish meaningful peaks from noise in the LFP signal. In this GUI, peak detection thresholds can be configured through the Menu Bar and are a key parameter in identifying spike events.

    Window size  
        The time segment (e.g., 10 seconds) used for analyzing continuous data streams.