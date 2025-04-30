Terminology
===========

.. glossary::

    Seizure-Like Event (SLE)
        A burst of abnormal electrical activity detected in brain slice recordings; used here as a basic unit of analysis.

    Multi-Electrode Array (MEA)
        A platform with many electrodes that record electrical signals from biological tissues like brain slices.

    Electrode
        A physical recording site on the Multi-Electrode Array (MEA) that picks up electrical signals from neural tissue. Each electrode captures local voltage changes from nearby neurons.

    Channel
        A data stream corresponding to a single electrode's recording. In the GUI, each electrode is associated with one channel, which carries the digitized signal data from that electrode.

    Raster plot
        A graphical representation showing the timing of spikes (action potentials) recorded across multiple electrodes. Each row represents one electrode, and each tick mark represents a detected spike at a specific time. Useful for visualizing patterns of neuronal activity across the array.

    Threshold detection
        A method to identify when a signal crosses a pre-set voltage or frequency limit, used to detect seizures.
    
    Local Field Potential (LFP)
        Local Field Potential (LFP) signals showing low-frequency voltage changes from groups of neurons, useful for spotting discharges and seizure-like events.

    Spike
        A rapid increase in voltage that often corresponds to neuronal firing.

    Burst
        A cluster of spikes that occur close together in time.

    Burst detection
        A method of identifying clusters of rapid spikes that may indicate heightened neural activity, sometimes preceding a seizure.

    Discharge
        A brief period of increased electrical activity recorded from neural tissue. In this GUI, a discharge typically refers to a localized burst of electrical signals detected on one or more electrodes. Discharges may represent isolated neuronal events or parts of larger seizure-like episodes (SLEs). The GUI analyzes discharges to detect patterns of abnormal neural activity, such as seizures or excessive synchrony between neurons.

    Baseline
        The level of electrical activity recorded when the tissue is in a resting or non-seizure state. Used as a reference for detecting discharges and SLEs.

    Synchronous activity
        When many electrodes detect similar signals at nearly the same time, indicating widespread neural coordination (often seen in seizures).

    Amplitude
        The strength (height) of a signal measured in millivolts (mV).
    
    Artifact
        Noise or signal distortion in recordings that does not represent true biological activity.
    
    Artifact rejection
        The process of removing or ignoring non-biological noise (e.g., mechanical vibration, electrical interference) during analysis.
    
    Window size
        The time segment (e.g., 10 seconds) used for analyzing continuous data streams.
    
    Metadata panel
        A summary display that shows key information about the recording file, such as the total duration, number of electrodes, sampling rate, and processing status. Useful for quickly verifying file properties before analysis.

    GUI (Graphical User Interface)
        The visual interface that allows users to interact with the software without using command-line commands.

    Discharge event
        A brief burst of electrical activity detected in a localized region of the brain slice. In the context of this GUI, a discharge event is typically detected using amplitude or frequency thresholds on Local Field Potential (LFP) signals.

    Discharge propagation
        The spread of a discharge event across the electrode array over time. It reflects the spatial and temporal recruitment of neural populations and is visualized using false color maps and LFP traces from multiple channels.

    Frames
        A single time point in the visualization or video output of the GUI, corresponding to a fixed time interval (e.g., 1 ms). Multiple frames make up a time-resolved representation of activity across the MEA.

    Nyquist frequency
        The highest frequency that can be reliably detected in a sampled signal, equal to half the sampling rate. For example, if MEA data is sampled at 10 kHz, the Nyquist frequency is 5 kHz. Frequencies above this cause aliasing and are not accurately represented.

    Aliasing  
        A signal distortion that occurs when a signal is sampled at too low a rate to capture its frequency content accurately. Frequencies higher than the Nyquist frequency appear as lower-frequency artifacts in the data, potentially causing misleading results in spike or oscillation detection.

    DBSCAN algorithm
        Density-Based Spatial Clustering of Applications with Noise — a machine learning algorithm that groups data points into clusters based on their density. In this GUI, DBSCAN may be used to identify spatial clusters of electrodes involved in a discharge or seizure event.

    Spectrogram
        A visual representation of how the frequency content of a signal changes over time. In neuroscience, spectrograms are often used to detect shifts in power across frequency bands during seizure events or other dynamic network activity.
