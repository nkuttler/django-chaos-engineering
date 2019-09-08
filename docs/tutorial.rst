=========================
Running chaos experiments
=========================

Planning an experiment
======================

Chaos experiments should be repeatable, limited in scope, and have measurable
results. One strategy to run them is:

1. Determine the failure you want to introduce, and its scope.
2. Form a hypothesis how your application will react and determine a log metric
   that will reflect the failure.
3. Plan remediation steps that bring the behavior back to normal
4. Run the experiment, start the failure with `djangochaos` by
   creating or enabling an action.
5. Verify the application's reaction and the metric.
6. Validate that applying the remediation steps bring behavior and metrics back
   to the normal state. With `djangochaos` this  can be achieved by disabling or
   deleting the action.
7. Develop a fix for the measured failure.
8. Repeat the experiment and verify that the failure doesn't happen again.

An experiment can also be run as a practical exercise for your developers and
ops people: Introduce the failure, have them detect it, figure out the
remediation steps, and deploy a fix. `Djangochaos` stores chaos actions in the
database, so nobody should look at those models during the exercise.

Examples of djangochaos experiments
===================================

This section contains examples that can help you to get started with your
experiments.

1 .Slow responses on a single API endpoint
------------------------------------------

This idea is similar to the one in experiment 1, but the failure probably needs
to be handled differently.

.. code-block:: shell

   manage.py chaos --create response --create-args slow "your_view_name" 1s 10s

This will slow down responses on the view to take between one and ten seconds.

2. Permission problem on single API endpoint
--------------------------------------------

The experiment's action is to return `401` responses from an API endpoint.
Ideally the endpoint is one of several used on a page, and the failure breaks
the frontend. If it doesn't, congratulations, you already have graceful failure.

.. code-block:: shell

   manage.py chaos create return "your_view_name" 401

After running this command, your application will start to return `401` response
codes for the specified view. The fix is to implement graceful failure in the
frontend. To remediate the behavior run one of:

.. code-block:: shell

   manage.py chaos disable response "your_view_name"
   manage.py chaos disable --all response

3. Random failures throughout the system
----------------------------------------

If you're just getting started with chaos engineering you might want to get an
overview which problems random failures can cause. To see this use:

.. code-block:: shell

   manage.py chaos storm --user <yourusername>
