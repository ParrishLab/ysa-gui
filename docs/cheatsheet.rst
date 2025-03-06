Cheat Sheet
===========

.. toctree::
   :maxdepth: 4
   :hidden:

   self

.. important::
   Still need to write the user guide.

Testing
-------

List of headers with links to them:
  - :ref:`header_2`Header
  - :ref:`Table`
  - :ref:`table_header`

.. _header_2:

Testing - Header 2
~~~~~~~~~~~~~~~~~~

For testing, you can use the following command:

.. code-block:: bash

    python -m unittest discover -s tests

Or, if you have `tox` installed, you can run the following command:

.. code-block:: bash

    tox

.. code-block:: python

    def find_discharges(self):
        self.set_custom_region()
        start, stop = self.custom_region

        lasso_selected_cells = [
            (cell.row + 1, cell.col + 1)
            for cell in self.grid_widget.get_lasso_selected_cells()
        ]
        if len(lasso_selected_cells) > 0:
            print("Finding discharges in highlighted cells")
            self.discharge_finder = DischargeFinder(
                self.data, lasso_selected_cells, self.signal_analyzer, start, stop
            )
        else:
            print("Finding discharges in all active cells")
            self.discharge_finder = DischargeFinder(
                self.data, self.active_channels, self.signal_analyzer, start, stop
            )
        self.discharge_finder.finished.connect(self.on_discharge_finder_finished)
        self.discharge_finder.start()

.. _table-header:
Table
-----

+------------------------+------------+----------+----------+
| Header row, column 1   | Header 2   | Header 3 | Header 4 |
| (header rows optional) |            |          |          |
+========================+============+==========+==========+
| body row 1, column 1   | column 2   | column 3 | column 4 |
+------------------------+------------+----------+----------+
| body row 2             | ...        | ...      |          |
+------------------------+------------+----------+----------+

This is a paragraph that contains `a link`_.

.. _a link: https://domain.invalid/

.. seealso::

   This is an example of a ``see also`` admonition.


Original Title
================

The page now scrolls down here.

.. _header_2:
Header Test 2
================


.. code-block:: python

  def my_function(my_arg, my_other_arg):
      """A function just for me.

      :param my_arg: The first of my arguments.
      :param my_other_arg: The second of my arguments.

      :returns: A message (just for me, of course).
      """


.. image:: _static/test_screenshot.png

Lorem ipsum [#f1]_ dolor sit amet ... [#f2]_

.. rubric:: Footnotes

.. [#f1] Text of the first footnote.
.. [#f2] Text of the second footnote.
