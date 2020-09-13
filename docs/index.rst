===========
Djangochaos
===========

.. toctree::
   :caption: Contents

   install
   tutorial
   changelog
   developing
   class_reference

`django_chaos_engineering` allows Django developers to quickly run simple `chaos
engineering <https://en.wikipedia.org/wiki/Chaos_engineering>`_ experiments.
Obviously a Django application can only create errors at the Django level, so
the experiments you can run with `django_chaos_engineering` are limited in scope.

You will need to use other tools to experiment on an infrastructure level, see
also the section on :ref:`limitations <design>`.

Use cases
=========

If your Django site uses JavaScript heavily and has a frontend that consumes
multiple API endpoints for one page you can use `django_chaos_engineering` to
simulate the failure of individual endpoints. This can be useful for frontend
experiments, especially assuming you use e.g. load balancers or multiple data
sources in production where failure of single endpoints is plausible.

Another scenario where this package can be useful is if you have flexible
permissions on your API and incorrect permissions could block access to some
endpoints.

.. _design:

Design decisions and limitations
================================

Chaos actions are Django models. It's the most convenient way to have a
configured action usable from everywhere in your stack. The assumption is that
your Django project runs on multiple worker nodes and that configuring chaos
actions on each one of them is not practical. Using a model we can also manage
chaos experiments from the Django admin area or with management commands.

I realize that adding models to a production database is not something everybody
is comfortable with, but when you get to the point that you want to run this app
in production you could either get in touch for some refactoring ideas or hire
me to implement the necessary changes.

Currently there are two methods of running chaos actions:

1. A middleware that brings chaos to requests/views
2. A database router that brings chaos to database queries

I would love to introduce other kinds of actions, e.g. errors connecting to
remote services and modifying data returned from such services, etc. But it
seems like such experiments would better be done with other tools. It might be
possible to create some of these effects by providing e.g. a `@chaos` decorator,
but having to modify the source code of an application in several places to run
chaos experiments sounds too intrusive to me.

If you want to run tests on your infrastructure, you can try tools like
`toxiproxy <https://github.com/shopify/toxiproxy>`_ and `pumba
<https://github.com/alexei-led/pumba>`_.

Roadmap
-------

Things I've been thinking about:

- Chaos actions for celery tasks
