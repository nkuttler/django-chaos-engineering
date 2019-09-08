from io import StringIO
from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from djangochaos import mock_data, models
from djangochaos.management.commands.chaos import STORM_KEY, STORM_VALUE


class OutsMixin:
    """
    Reusable test mixin for all action types.
    """

    def setUp(self):
        self.out = StringIO()
        self.err = StringIO()


class HelpTest(OutsMixin, TestCase):
    """
    Ensure we get fewer argparse errors.
    """

    def _test_help_smoke_test(self, command):
        with self.assertRaises(SystemExit) as ex:
            call_command("chaos", command, "--help", stdout=self.out, stderr=self.err)
        self.assertEqual(0, ex.exception.code)

    def test_help_smoke_test(self):
        for command in ["create_response", "create_db", "list", "storm", "dump"]:
            self._test_help_smoke_test(command)


class OutputMixin:
    """
    Simple tests that verify if stderr/stdout are empty/not empty.
    """

    def _test_output_equals(self, output, value, *args):
        """
        Ensure stdout is empty for list commands.
        """
        call_command("chaos", self.command, *args, stdout=self.out, stderr=self.err)
        self.assertEqual(
            value,
            output.getvalue(),
            "Output does not match: {}".format(output.getvalue()),
        )

    def _test_output_not_equals(self, output, value, *args):
        """
        Ensure stdout is empty for list commands.
        """
        call_command("chaos", self.command, *args, stdout=self.out, stderr=self.err)
        self.assertNotEqual(
            value,
            output.getvalue(),
            "Output does not match: {}".format(output.getvalue()),
        )


class CommandListTest(OutsMixin, OutputMixin, TestCase):
    command = "list"

    def test_list_stdout_empty(self):
        self._test_output_equals(self.out, "")

    def test_list_stderr_empty(self):
        self._test_output_not_equals(self.err, "")

    def test_list_stdout_empty_more(self):
        self._test_output_equals(self.out, "", "--more")

    def test_list_stderr_empty_more(self):
        self._test_output_not_equals(self.err, "", "--more")

    def test_list_stdout_empty_excess(self):
        self._test_output_equals(self.out, "", "--excess")

    def test_list_stderr_empty_excess(self):
        self._test_output_not_equals(self.err, "", "--excess")

    def test_list_output_one_of_each_action(self):
        mock_data.make_action_db()
        mock_data.make_action_response()
        self._test_output_equals(self.err, "")
        self._test_output_not_equals(self.out, "")

    def test_list_by_model_stderr_empty(self):
        mock_data.make_action_db()
        mock_data.make_action_response()
        for model in models.model_choices:
            self._test_output_equals(self.err, "", "--models", model)
            self._test_output_not_equals(self.out, "", "--models", model)

    def test_list_with_kv_stderr_empty(self):
        key = models.ChaosKV.get_random_key()
        mock_data.make_action_db(config={key: "bar"})
        mock_data.make_action_response(config={key: "bar"})
        self.assertEqual(2, models.ChaosKV.objects.all().count())
        for model in models.model_choices:
            self._test_output_equals(self.err, "", "--models", model)
            self._test_output_not_equals(self.out, "", "--models", model)
            call_command("chaos", "list", stdout=self.out, stderr=self.err)


class GenericCommandTest(OutsMixin, TestCase):
    def test_nonsense(self):
        with self.assertRaises(CommandError):
            call_command("chaos", "foo", stdout=self.out, stderr=self.err)

    @patch("djangochaos.models.ChaosActionBase.dump")
    def test_dump_db(self, _dump):
        key = models.ChaosKV.get_random_key()
        action = mock_data.make_action_db(config={key: "bar"})
        call_command("chaos", "dump", "db", action.id, stdout=self.out, stderr=self.err)
        self.assertEqual(1, _dump.call_count)

    @patch("djangochaos.models.ChaosActionBase.dump")
    def test_dump_response(self, _dump):
        key = models.ChaosKV.get_random_key()
        action = mock_data.make_action_response(config={key: "bar"})
        call_command(
            "chaos", "dump", "response", action.id, stdout=self.out, stderr=self.err
        )
        self.assertEqual(1, _dump.call_count)

    def test_dump_response_without_mock(self):
        # For coverage
        key = models.ChaosKV.get_random_key()
        action = mock_data.make_action_response(config={key: "bar"})
        call_command(
            "chaos", "dump", "response", action.id, stdout=self.out, stderr=self.err
        )

    @patch("djangochaos.models.ChaosActionBase.dump")
    def test_dump_response_does_not_exist(self, _dump):
        call_command("chaos", "dump", "response", 123, stdout=self.out, stderr=self.err)
        self.assertEqual(0, _dump.call_count)


class CreateMixin:
    """
    This mixin runs commands that create chaos actions.
    """

    def _test_create_action_calls(self, verb, *args):
        """
        Test that create commands call the right mock method.
        """
        with patch(self.mocker) as _mock:
            call_command(
                "chaos",
                "create_{}".format(self.action_type),
                verb,
                *args,
                stdout=self.out,
                stderr=self.err,
            )
            self.assertFalse(self.err.getvalue(), self.err.getvalue())
            self.assertEqual(1, _mock.call_count)
            args, kwargs = _mock.call_args
            self.assertEqual(verb, kwargs["verb"])

    def _test_create_action_creates_objects(self, verb, *args):
        """
        Test that create commands create objects.
        """
        call_command(
            "chaos",
            "create_{}".format(self.action_type),
            verb,
            *args,
            stdout=self.out,
            stderr=self.err,
        )
        self.assertFalse(self.err.getvalue(), self.err.getvalue())
        self.assertEqual(1, self.cls.objects.filter(verb=verb).count())

    def test_create_slow_calls_mock(self):
        self._test_create_action_calls(models.verb_slow, "test_value")

    def test_create_raise_calls_mock(self):
        self._test_create_action_calls(models.verb_raise, "test_value")

    def test_create_slow_creates_objects(self):
        self._test_create_action_creates_objects(models.verb_slow, "test_value")
        self.assertEqual(1, self.cls.objects.all().count())

    def test_create_raise_creates_object(self):
        self._test_create_action_creates_objects(models.verb_raise, "test_value")
        self.assertEqual(1, self.cls.objects.all().count())

    def test_create_actions_with_kv(self):
        key = models.ChaosKV.get_random_key()
        self._test_create_action_creates_objects(
            models.verb_raise, "test_value", "--create-kv", key, "bar"
        )
        self.assertEqual(1, self.cls.objects.all().count())
        actions = self.cls.objects.filter(chaos_kvs__value="bar")
        self.assertEqual(1, len(actions))

    def test_storm_creates_actions(self):
        user = mock_data.make_user()
        call_command(
            "chaos", "storm", "--user", user.username, stdout=self.out, stderr=self.err
        )
        actions = self.cls.objects.all()
        self.assertEqual(len(self.cls.verb_choices), len(actions))

    def test_storm_creates_actions_with_kv(self):
        user = mock_data.make_user()
        call_command(
            "chaos", "storm", "--user", user.username, stdout=self.out, stderr=self.err
        )
        actions = self.cls.objects.filter(chaos_kvs__value=STORM_VALUE)
        self.assertEqual(len(self.cls.verb_choices), len(actions))

    def test_storm_creates_actions_with_probability(self):
        user = mock_data.make_user()
        call_command(
            "chaos",
            "storm",
            "--user",
            user.username,
            "--probability",
            77,
            stdout=self.out,
            stderr=self.err,
        )
        actions = self.cls.objects.filter(chaos_kvs__value=STORM_VALUE, probability=77)
        self.assertEqual(len(self.cls.verb_choices), len(actions))

    def test_storm_actions(self):
        mock_data.make_action_response()
        mock_data.make_action_db()
        mock_data.make_action_response(config={STORM_KEY: STORM_VALUE})
        mock_data.make_action_db(config={STORM_KEY: STORM_VALUE})
        call_command("chaos", "storm", "--end", stdout=self.out, stderr=self.err)
        actions = self.cls.objects.all()
        # As we only count one action class, only one object should exist
        self.assertEqual(1, len(actions))

    def test_storm_wrong_call_no_args(self):
        with self.assertRaises(CommandError):
            call_command("chaos", "storm", stdout=self.out, stderr=self.err)

    def test_storm_wrong_call_users_and_groups(self):
        with self.assertRaises(CommandError):
            call_command(
                "chaos",
                "storm",
                "--users",
                "foo",
                "--groups",
                "bar",
                stdout=self.out,
                stderr=self.err,
            )


class CreateResponseTest(CreateMixin, OutsMixin, TestCase):
    mocker = "djangochaos.mock_data.make_action_response"
    action_type = "response"
    cls = models.ChaosActionResponse

    def test_create_return_calls_mock(self):
        self._test_create_action_calls(models.verb_return, "test_view")

    def test_create_return_creates_object(self):
        self._test_create_action_creates_objects(models.verb_return, "test_view")


class CreateResponseDB(CreateMixin, OutsMixin, TestCase):
    mocker = "djangochaos.mock_data.make_action_db"
    action_type = "db"
    cls = models.ChaosActionDB
