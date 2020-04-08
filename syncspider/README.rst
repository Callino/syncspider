============
Syncspider
============

.. image:: ./static/description/icon_128.png

This module will allow you to set event trigger for create, update and unlink on any model.

Installation
============

To install this module, you need to:

Download the module and add it to your Odoo addons folder. Afterward, log on to
your Odoo server and go to the Apps menu. Trigger the debug mode and update the
list by clicking on the "Update Apps List" link. Now install the module by
clicking on the install button.

Upgrade
============

To upgrade this module, you need to:

Download the module and add it to your Odoo addons folder. Restart the server
and log on to your Odoo server. Select the Apps menu and upgrade the module by
clicking on the upgrade button.

Configuration
=============

Configuration of Sync hooks is needed for this module to work. These can be set here: Settings/Technical/Database Structure/Sync Hooks

You'll need tobe in group Other/Syncspider Web Hooks for this.

.. image:: ./static/description/s3.png

Setup a hook by setting the "Record Reference" to the desired model. You can limit to a single record by giving a "Record ID". 0 Means all records of the model.
You can choose any of the Triggers, but keep in mind they'd all call the same webhook URL. So if you'd like to trigger a different call for create than for unlink setup 2 sync hooks.
"Webhook" is the URL which will be called when an event triggers.

.. image:: ./static/description/s1.png

The list at the bottom of the for will fill up over time with information about the state of your events.

.. image:: ./static/description/s2.png

Usage
=============

Once Sync Hooks are configured no further steps are required, odoo will continue to send requests to the set webhooks automatically.

Credits
=======

Contributors
------------

* Wolfgang Pichler <wpicher@callino.at>
* Gerhard Baumgartner <gbaumgartner@callino.at>

Author & Maintainer
-------------------

This module is maintained by `Syncspider <https://www.syncspider.com/>`_.

If you want to get in touch please contact us via mail
(hello@syncspider.com) or visit our website (https://syncspider.com).
