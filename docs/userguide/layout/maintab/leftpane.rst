=========
Left Pane
=========

The Left Pane of the GUI allows you to interact directly with the MEA grid and visualize :term:`Local Field Potential (LFP)` activity. You can also view spike timing data through the :term:`Raster Plot`, assign channels to trace plots, and access grouping and sorting tools.

For a full overview of how to conduct an analysis using these features, we recommend starting with the :ref:`Walkthrough <walkthrough>` section.

.. _mea_grid:

MEA Grid
--------

After loading a ``.brw`` file and running either :ref:`quick_view` or :ref:`run_analysis`, the MEA grid will be populated with active channels (shown in light gray).

* Hover over a channel to view its ``(row, column)`` position.

* Click a channel to highlight it.

* Press ``1``, ``2``, ``3``, or ``4`` to assign that channel's trace to the corresponding plot in the Right Pane.

* Assigned channels will appear with markers on both the MEA grid and the associated trace plot.

Context Menus
~~~~~~~~~~~~~

Right-click on the MEA grid or use the :ref:`menu_bar` to access options such as:

* Changing the grid's visual appearance

* Saving the grid view as an image

* Exporting the animated grid as a video


.. _raster_plot:

Raster Plot
-----------

The raster plot shows spike activity across channels. Each row corresponds to a channel; each dot is a detected spike.

* **Blue dots** = spikes during seizures or :term:`Seizure-Like Event (SLE)`s

* **Orange dots** = spikes during :term:`Status Epilepticus (SE)` events

* **Black dots** = spikes outside seizure/SE periods

You can change the spike :term:`Detection threshold` using the ``Edit Raster Settings`` button.

Mouse controls:
^^^^^^^^^^^^^^^

- ``Left click + drag`` = pan

- ``Right click + drag`` = zoom (horizontal or vertical)

- ``Scroll wheel`` = zoom in/out

- ``Left click`` on a spike = jump playback to that time, select the channel, and optionally assign to a trace plot with ``1``-``4``

- Hover = view timestamp and channel info for any spike event


.. _row_order:

Row Order
~~~~~~~~~

Right-clicking the raster plot opens sorting options for the channel rows:

* Default: MEA grid order (left to right, top to bottom)

* If analysis has been run, you can sort by:

  * Order of entrance into an SE event

  * Order of entrance into a seizure event

  * Clustered entrance times into an SE event


Spatial Groups
~~~~~~~~~~~~~~

To define spatial regions (e.g., hippocampus vs neocortex):

1. Click ``Create Groups`` at the bottom of the Left Pane.

2. Use lasso selection to define regions.

Lasso controls:
^^^^^^^^^^^^^^^

* ``Left click + drag`` = draw a selection

* ``c`` = clear selection

* ``z`` = undo

* ``Shift + z`` = redo

* ``Enter`` or click ``Save Group`` = confirm a group

* ``Confirm`` = save all groups and close the window

.. tip::
  You can click ``Toggle Color Mode`` to visualize clusters or groups with distinct colors.

Once groups are created, tooltips will display group names. For statistics, switch from the ``Main`` tab to the ``Stats`` tab.
