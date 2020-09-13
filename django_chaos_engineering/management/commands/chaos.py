"""
Copyright (c) 2019 Nicolas Kuttler, see LICENSE for details.
"""

from itertools import chain

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.urls import exceptions
from django.utils.translation import gettext as _

from django_chaos_engineering import mock_data, models


#: For KV key for special actions
STORM_KEY = "creator"
#: For KV value for special actions
STORM_VALUE = "storm"

STORM_ENABLED = False


class Command(BaseCommand):
    """
    The `chaos` command is a way to interact with `django_chaos_engineering` from the
    command line.
    """

    def add_arguments(self, parser):
        # required kwargs not in python 3.5
        subparsers = parser.add_subparsers(title="commands", dest="command",)
        subparsers.required = True

        parser_create_response = subparsers.add_parser("create_response")
        parser_create_response.set_defaults(command="create_response")
        parser_create_response.add_argument(
            "verb",
            type=str,
            choices=models.ChaosActionResponse.verb_choices_str,
            help=_("The action's effect"),
        )
        parser_create_response.add_argument(
            "url_name", type=str, help=_("Url (by name) to act on"),
        )
        parser_create_response.add_argument(
            "--create-kv",
            type=str,
            nargs=2,
            action="append",
            help=_("KVs for the created action, see the documentation"),
            default=list(),
            metavar=("keyword", "value"),
        )

        parser_create_db = subparsers.add_parser("create_db")
        parser_create_db.set_defaults(command="create_db")
        parser_create_db.add_argument(
            "verb",
            type=str,
            choices=models.ChaosActionDB.verb_choices_str,
            help=_("The action's effect"),
        )
        parser_create_db.add_argument(
            "value", type=str, help=_("The value of the attribute to match"),
        )
        parser_create_db.add_argument(
            "--attribute",
            choices=models.ChaosActionDB.attr_choices_str,
            default=models.ChaosActionDB.attr_default,
            type=str,
            help=_("The model attribute to match"),
        )
        parser_create_db.add_argument(
            "--create-kv",
            type=str,
            nargs=2,
            action="append",
            help=_("KVs for the created action, see the documentation"),
            default=list(),
            metavar=("keyword", "value"),
        )

        parser_list = subparsers.add_parser("list")
        parser_list.set_defaults(command="list")
        parser_list.add_argument("--verb", type=str, help=_("Filter by verb"))
        parser_list.add_argument(
            "--models",
            nargs="+",
            type=str,
            choices=models.model_choices,
            default=models.model_choices,
            help=_("Filter by action model"),
        )
        parser_list.add_argument(
            "--more", "-m", action="store_true", help=_("Dump more data")
        )
        parser_list.add_argument(
            "--excess", "-e", action="store_true", help=_("Dump excessive data")
        )

        parser_dump = subparsers.add_parser("dump")
        parser_dump.set_defaults(command="dump")
        parser_dump.add_argument(
            "model", type=str, choices=models.model_choices, help=_("Action model"),
        )
        parser_dump.add_argument("id", type=int, help=_("Object id"))
        parser_dump.add_argument("--more", action="store_true", help=_("Dump more data"))
        parser_dump.add_argument(
            "--excess", action="store_true", help=_("Dump excessive data")
        )

        if STORM_ENABLED is True:
            parser_storm = subparsers.add_parser("storm")
            parser_storm.set_defaults(command="storm")
            parser_storm.add_argument(
                "--users",
                nargs="+",
                type=str,
                help=_("The users to have a party for"),
                default=User.objects.none(),
            )
            parser_storm.add_argument(
                "--groups",
                nargs="+",
                type=str,
                help=_("The groups to have a party for"),
                default=Group.objects.none(),
            )
            parser_storm.add_argument(
                "--end", action="store_true", help=_("Delete existing storm actions")
            )
            parser_storm.add_argument(
                "--probability", type=int, help=_("Probability %% of created actions")
            )

    def handle(self, *args, **options):
        cmd = options["command"]
        if cmd == "list":
            self.list(
                verb=options["verb"],
                include_models=options["models"],
                more=options["more"],
                excess=options["excess"],
            )
        if cmd == "dump":
            self.dump(
                model=options["model"],
                id=options["id"],
                more=options["more"],
                excess=options["excess"],
            )
        elif cmd == "create_response":
            self.create_response(
                options.get("url_name"),
                options.get("verb"),
                create_kv=options.get("create_kv", []),
            )
        elif cmd == "create_db":
            config = {}
            for kv in options.get("create_kv", []):
                config[kv[0]] = kv[1]
            self.create(
                action_type="db",
                verb=options.get("verb"),
                act_on_attribute=options.get("attribute"),
                act_on_value=options.get("value"),
                config=config,
            )
        elif cmd == "storm":
            if options["end"] is True:
                self.storm_end()
            else:
                self.storm_start(
                    options["users"], options["groups"], options["probability"]
                )

    def create_response(self, url_name, verb, create_kv=None):
        config = {}
        create_kv = create_kv or []
        for kv in create_kv:
            config[kv[0]] = kv[1]
        try:
            reverse(url_name)
        except exceptions.NoReverseMatch:
            self.stderr.write(
                "Could not reverse name {}.. still continuing".format(url_name)
            )
        self.create(
            action_type="response", verb=verb, act_on_url_name=url_name, config=config,
        )

    def list(self, verb, include_models, more=False, excess=False):
        if "response" in include_models:
            actions_response = models.ChaosActionResponse.objects.all()
        else:
            actions_response = models.ChaosActionResponse.objects.none()
        if "db" in include_models:
            actions_db = models.ChaosActionDB.objects.all()
        else:
            actions_db = models.ChaosActionDB.objects.none()
        actions = list(chain(actions_response, actions_db))
        for action in actions:
            for line in action.dump(more=more, excess=excess):
                self.stdout.write(line)
        if not actions:
            self.stderr.write(_("No chaos actions found"))

    def dump(self, model, id, more=False, excess=False):
        if model == "db":
            cls = models.ChaosActionDB
        elif model == "response":
            cls = models.ChaosActionResponse
        try:
            for line in cls.objects.get(id=id).dump(more=more, excess=excess):
                self.stdout.write(line)
        except cls.DoesNotExist:
            self.stderr.write("Object not found")

    def create(self, **kwargs):
        mockers = {
            "response": mock_data.make_action_response,
            "db": mock_data.make_action_db,
        }
        mocker = mockers.get(kwargs.pop("action_type"))
        action = mocker(**kwargs)
        self.stdout.write(_("Created action: {}".format(action)))

    def storm_end(self):
        kvs = models.ChaosKV.objects.filter(key=STORM_KEY, value=STORM_VALUE)
        models.ChaosActionDB.objects.filter(chaos_kvs__in=kvs).delete()
        models.ChaosActionResponse.objects.filter(chaos_kvs__in=kvs).delete()

    def storm_start(self, users, groups, probability=None):
        """
        Create some wildcard actions with relatively low probability.

        The assumption is that every page does 30 db queries on average, and
        that we want a failure for every 10th response.

        With NV being the number of verbs of the action we want:

        - For db router actions: 0.333%
        - For middleware actions: 10%

        All actions created here get a KV object associated with them to make
        it possible to delete them easily.
        """
        if users and groups:
            raise CommandError("--user and --group can not be used together")

        users = User.objects.filter(username__in=users)
        groups = Group.objects.filter(name__in=groups)
        if not users and not groups:
            raise CommandError("Could not find any matching users/groups by given names")

        probability = probability or 10 / len(
            models.ChaosActionResponse.verb_choices_str
        )
        for verb in models.ChaosActionResponse.verb_choices_str:
            action = mock_data.make_action_response(
                verb=verb,
                act_on_url_name="",
                for_users=users,
                for_groups=groups,
                probability=probability,
                config={STORM_KEY: STORM_VALUE},
            )
            self.stdout.write("Created response action\t{}".format(action))

        probability = probability or 1 / 30 / len(
            models.ChaosActionResponse.verb_choices_str
        )
        for verb in models.ChaosActionDB.verb_choices_str:
            action = mock_data.make_action_db(
                verb=verb,
                act_on_attribute=models.attr_choices_db["attr_app_label"]["attribute"],
                act_on_value="",
                for_users=users,
                for_groups=groups,
                probability=probability,
                config={STORM_KEY: STORM_VALUE},
            )
            self.stdout.write("Created dbroute action\t{}".format(action))
