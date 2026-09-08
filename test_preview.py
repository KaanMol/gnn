import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from goud_runtime import GoudRuntime
from preview import Application
from semantics import operation


class Translator:
    model = "fixture"

    def translate(self, utterance, context):
        return {"operations": [operation("assert", "Mira", "is", "person")]}


class PreviewTests(unittest.TestCase):
    def test_teaching_and_sensor_evidence_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = Path(directory) / "preview.json"
            app = Application(Translator(), memory)
            app.action({"action": "chat", "message": "Mira is a person."})
            app.action({"action": "explore"})
            restored = Application(Translator(), memory)
            before, after = app.state(), restored.state()
            before.pop('state_version'); after.pop('state_version')
            self.assertEqual(before, after)
            self.assertEqual(len(restored.state()["experiments"]), 1)
            self.assertIn(["is", "Mira", "person"], restored.state()["facts"])

    def test_invalid_action_leaves_memory_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = Path(directory) / "preview.json"
            app = Application(Translator(), memory)
            with self.assertRaises(ValueError):
                app.action({"action": "invent_sensor_reading"})
            self.assertFalse(memory.exists())

    def test_reuses_desktop_sidecar_without_spawning_or_stopping_it(self):
        runtime = GoudRuntime()
        with patch.object(runtime, "model_at", return_value="gemma.gguf"), patch("goud_runtime.subprocess.Popen") as spawn:
            self.assertEqual(runtime.connect(), ("http://127.0.0.1:18766", "gemma.gguf"))
            runtime.close()
        spawn.assert_not_called()

    def test_small_view_preserves_complete_evidence_on_demand(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Application(Translator(), Path(directory)/'preview.json')
            try:
                large = {'raw': 'evidence' * 100000}
                record = {'source':'test','original':'Example','answer':'Done'*10000, 'translation':{'kind':'graph_package','entries':large},
                          'trace':[{'node':'n1','operation':'emit','result':'x'*20000,'evidence':large}]}
                app.session.language_records.append(record)
                row = app.state()['language'][-1]
                self.assertLess(len(json.dumps(row)), 7500)
                self.assertTrue(row['truncated'])
                self.assertEqual(app.record('experience.language', 0), record)
                with self.assertRaises(ValueError): app.record('arbitrary.namespace', 'key')
            finally:
                app.session.store.close()

    def test_delta_sends_only_changed_sections_and_message_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Application(Translator(), Path(directory)/'preview.json')
            try:
                first = app.state()
                unchanged = app.state(first['state_version'])
                self.assertEqual(set(unchanged), {'state_version','partial'})
                reply = app.action({'action':'chat','message':'Mira is a person','state_version':first['state_version']})['state']
                self.assertTrue(reply['partial'])
                self.assertNotIn('procedures', reply)
                self.assertNotIn('language', reply)
                self.assertEqual(reply['language_patch']['length'], 1)
                self.assertEqual(reply['language_patch']['items'][0]['value']['original'], 'Mira is a person')
                self.assertIn(['is','Mira','person'], reply['facts'])
                # A new/expired client gets a complete view, including restart.
                reset = app.state('expired-version')
                self.assertNotIn('partial', reset)
                self.assertIn('procedures', reset)
            finally:
                app.session.store.close()


if __name__ == "__main__":
    unittest.main()
