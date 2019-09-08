Developing djangochaos
======================

You want to hack this code? Great! Install all dependencies::

    pip install -r requirements.txt

Running test
------------

Test coverage should not go down. The raw number doesn't really mean anything as
it's easy to increase coverage with meaningless test, and 100% coverage doesn't
mean all planned features exist or work as expected. Try to write meaningful
tests that verify the results of executing code, not tests that simply execute
the code::

    python manage.py test

To build the coverage and static code analysis reports use the following command
instead::

    make test

Documentation
-------------

Build the documentation locally::

    make docs

Coding style
------------

You should run black and docformatter before committing any code. There is a git
hook that will ensure this has happened::

    make .git/hooks/pre-commit

Or just run the tools with `make`::

    make style

Internationalization
--------------------

Strings are internationalized, run `make messages` and commit the changes if you
update or add any strings.

Type hints
----------

This is the first time I'm seriously using type hints on a code base. They seem
good for documentation purposes, and that's why I use them. They may be useful
for other things too.
