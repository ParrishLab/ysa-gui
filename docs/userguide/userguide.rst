User Guide
==========

👋 Welcome to the YSA User Guide!

This guide is organized into several sections covering installation, setup, and how to use the application's main features.

If you're new to YSA, start with the :ref:`installation` section to set up the application.  
Then, continue with the :ref:`walkthrough` for a step-by-step guide through opening files, running analyses, and viewing results.

.. tip::
   🔍 Use the search bar at the top of the page to quickly find specific topics across the guide.


Contents
--------
Getting Started
~~~~~~~~~~~~~~~

📦 :doc:`Installation <installation>`
   Set up YSA on your machine

🛠️ :doc:`Configuration <configuration>`  
   Adjust settings for your data and recordings

🛣️ :doc:`Walkthrough <analysis/walkthrough>`  
   Step-by-step guide to running analyses


Advanced Features
~~~~~~~~~~~~~~~~~

🗺️ :doc:`Layout Overview <layout/layout>`  
   Explore the structure of YSA — how menus, panes, and tabs fit together.

   ⚙️ :doc:`Menu Bar <layout/menubar>`  
      Learn what each menu item does — including access to file operations, configuration, and help.

   🧮 :doc:`Main Tab Overview <layout/maintab/maintab>`  
      Understand the role of the main analysis tab and its sub-tools.

      🖱️ :doc:`Left Pane <layout/maintab/leftpane>`  
         Interact with the MEA grid, select electrodes, and view the false color map or the raster plot.

      📊 :doc:`Right Pane <layout/maintab/rightpane>`  
         Analyze visualizations using tools like trace plots and the control panel.

🧭 :doc:`Discharge Propagation Tracking <analysis/dischargetracking>`  
   Visualize how seizure-like events spread across the slice — frame-by-frame across time and space.


.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   installation
   configuration
   analysis/walkthrough

.. toctree::
   :maxdepth: 3
   :caption: Advanced Features
   :hidden:

   layout/layout
   analysis/dischargetracking
