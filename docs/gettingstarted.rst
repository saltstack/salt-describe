###############
Getting Started
###############


Salt describe is an extension to Salt that allows a user to automatically
create the SLS files for them based on the current state of the system.


Pre-Requisites
==============
Salt describe requires the Salt master and Salt minion. The Salt master
needs to be installed where you plan to run Salt describe, and the
Salt minion needs to be installed on all the systems you plan on targeting
with Salt describe.

1. Installing Salt Master and Salt Minion
-----------------------------------------
You can install both the Salt master and Salt minion using the onedir packages
or using a pip install. If you want to use the onedir packages, please follow
the installation instructions from the `install guide <https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/index.html>`_

If you want to install using the pip packages, you only need to run the following
command:

.. code-block:: bash

   # pip install salt


2. Start Salt master and Salt minion services
---------------------------------------------
If you installed the onedir packages, please refer to the same `install guide <https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/index.html>`_
on instructions on how to start the services for both Salt master and Salt minion
for your given OS.

If you are using the pip packages you can start the services using the following commands:

To start the Salt master in the background

.. code-block:: bash

   # salt-master -d

To start the Salt minion in the background

.. code-block:: bash

   # salt-minion -d


Installing Salt describe
========================

Salt describe is hosted as a pip package on pypi, so you only need to install the pip package
for the install.

If you are using onedir Salt packages, you need to run the following:

.. code-block:: bash

   # salt-pip install salt-describe

If you are using the Salt pip packages, you need to run the following:

.. code-block:: bash

   # pip install salt-describe


How to use Salt describe
========================

Now you are ready to start using Salt describe, and auto generating your SLS files for all
of the systems you want to manage. Salt describe is a Salt runner, so you need to use the cli
tool ``salt-run`` to interact with the extension. The command looks like the following:


.. code-block:: bash

   # salt-run describe.<module> <minion>

So for example, if you have a minion named ``poc-minion`` and you want to auto generate the
``pkg.installed`` stated you would need to run the following:

.. code-block:: bash

   # salt-run describe.pkg poc-minion
   Generated SLS file locations:
       - /srv/salt/poc-minion/pkg.sls

This command queries the poc-minion for all currently installed packages and creates the ``pkg.installed``
state in the file location <file_roots>/<minion>/<module>.sls. In this example the file is located
at /srv/salt/poc-minion/pkg.sls

If you open the file you will see all the currently installed packages and versions listed in the state:

.. code-block:: yaml

    installed_packages:
      pkg.installed:
        - pkgs:
          - a52dec: 0.7.4-11
          - aalib: 1.4rc5-14
          - accountsservice: 22.08.8-2


If you want to add a new package, for example php, you only need to add it to the list of the already
installed packages:


.. code-block:: yaml

    installed_packages:
      pkg.installed:
        - pkgs:
          - php
          - a52dec: 0.7.4-11
          - aalib: 1.4rc5-14
          - accountsservice: 22.08.8-2

Now when you run this state against your minion, it will verify the currently installed packages are installed
and also install the new php packages:


.. code-block:: bash

    # salt poc-minion state.apply poc-minion.pkg
    poc-minion:
    ----------
              ID: installed_packages
        Function: pkg.installed
          Result: True
         Comment: The following packages were installed/updated: php
                  The following packages were already installed: a52dec=0.7.4-11, aalib=1.4rc5-14, accountsservices=22.08.8-2
         Started: 08:53:13.583733
        Duration: 2300.737 ms
         Changes:
                  ----------
                  php:
                      ----------
                      new:
                          8.1.13-4
                      old:

    Summary for poc-minion
    ------------
    Succeeded: 1 (changed=1)
    Failed:    0
    ------------
    Total states run:     1
    Total run time:   2.301 s
