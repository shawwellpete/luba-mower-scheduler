"""Exercise the generic examples with synthetic state; no mower is contacted."""
import ast
import json
import re
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import yaml
from jinja2.nativetypes import NativeEnvironment

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2030, 5, 10, 12, tzinfo=timezone.utc)


def timestamp(value, default=None):
    try:
        if isinstance(value, (float, int)):
            return value
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).timestamp()
    except (ValueError, TypeError):
        return default


class States:
    def __init__(self, values=None):
        self.values = values or {}

    def __call__(self, entity):
        return self.values.get(entity, "unknown")

    def __getitem__(self, entity):
        if entity not in self.values:
            return None
        return SimpleNamespace(state=self.values[entity], entity_id=entity)


def environment(values=None, attributes=None):
    states = States(values)
    attrs = attributes or {}
    env = NativeEnvironment()
    env.globals.update(states=states, now=lambda: NOW, timedelta=timedelta,
        as_timestamp=timestamp, is_state=lambda e, v: states(e) == v,
        state_attr=lambda e, a: attrs.get(e, {}).get(a),
        is_number=lambda v: bool(re.fullmatch(r"-?\d+(?:\.\d+)?", str(v))),
        dict=dict)
    env.filters["to_json"] = json.dumps
    def from_json(value, default=None):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return default
    env.filters["from_json"] = from_json
    env.filters["timestamp_custom"] = lambda v, fmt, local=True: datetime.fromtimestamp(float(v), timezone.utc).strftime(fmt)
    return env, states


def render(env, text, **context):
    if text == "":
        return ""
    value = env.from_string(text).render(**context)
    if isinstance(value, str):
        value = value.strip()
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass
    return value


class Runner:
    """Small action interpreter for the subset used by the dispatch examples."""
    def __init__(self, values, confirmed=True):
        self.env, self.states = environment(values)
        self.context = {"zone": "lawn_1", "source": "schedule"}
        self.actions = []
        self.confirmed = confirmed

    def render(self, value):
        if isinstance(value, str):
            return render(self.env, value, **self.context)
        if isinstance(value, dict):
            return {k: self.render(v) for k, v in value.items()}
        return value

    def condition(self, c):
        if isinstance(c, str):
            return bool(self.render(c))
        if c["condition"] == "template":
            return bool(self.render(c["value_template"]))
        return self.states(self.render(c["entity_id"])) == c["state"]

    def run(self, sequence):
        for step in sequence:
            if "variables" in step:
                for key, value in step["variables"].items():
                    self.context[key] = self.render(value)
            elif "condition" in step:
                if not self.condition(step):
                    return False
            elif "stop" in step:
                return False
            elif "if" in step:
                branch = step.get("then", []) if all(self.condition(c) for c in step["if"]) else step.get("else", [])
                if self.run(branch) is False:
                    return False
            elif "repeat" in step:
                for index, item in enumerate(step["repeat"]["for_each"], 1):
                    self.context["repeat"] = {"index": index, "item": item}
                    if self.run(step["repeat"]["sequence"]) is False:
                        return False
            elif "wait_template" in step:
                self.context["wait"] = {"completed": bool(self.render(step["wait_template"]))}
            elif "action" in step:
                action = step["action"]
                target = self.render(step.get("target", {}).get("entity_id", ""))
                data = self.render(step.get("data", {}))
                self.actions.append((action, target, data))
                if action == "button.press" and self.confirmed:
                    self.states.values["lawn_mower.mower"] = "mowing"
                if action in {"input_datetime.set_datetime", "input_text.set_value"}:
                    self.states.values[target] = data.get("datetime", data.get("value"))
        return True


class ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {p.name: yaml.safe_load(p.read_text()) for p in ROOT.glob("*.yaml") if p.name != "configuration.yaml"}
        cls.scripts = cls.files["scripts.yaml"]
        cls.templates = cls.files["template.yaml"]

    def ready(self):
        return {"lawn_mower.mower":"docked", "input_boolean.do_not_mow":"off",
            "binary_sensor.mowing_conditions_blocked":"off", "button.mower_lawn_1":"unknown",
            "input_select.lawn_1_schedule":"once per week",
            "input_datetime.lawn_1_last_mow_1":"2030-05-01 10:00:00",
            "input_datetime.lawn_1_last_mow_2":"2030-04-24 10:00:00"}

    def logger(self, second=False):
        uid = "mowing_session_log_2" if second else "mowing_session_log"
        return next(s for t in self.templates for s in t.get("sensor", []) if s.get("unique_id") == uid)

    def test_templates_parse(self):
        env, _ = environment()
        def visit(v):
            if isinstance(v, dict):
                for item in v.values(): visit(item)
            elif isinstance(v, list):
                for item in v: visit(item)
            elif isinstance(v, str) and ("{{" in v or "{%" in v):
                env.parse(v)
        for value in self.files.values(): visit(value)

    def test_unknown_existing_button_is_valid_and_history_follows_start(self):
        runner = Runner(self.ready())
        self.assertTrue(runner.run(self.scripts["mow_lawn"]["sequence"]))
        names = [a[0] for a in runner.actions]
        self.assertLess(names.index("button.press"), names.index("input_datetime.set_datetime"))
        self.assertEqual(runner.states("input_datetime.lawn_1_next_time"), "2030-05-17 12:00:00")
        self.assertEqual(runner.states("input_text.last_lawn_mowed"), "Lawn 1")

    def test_timeout_does_not_record_start_or_weekly_interval(self):
        runner = Runner(self.ready(), confirmed=False)
        self.assertFalse(runner.run(self.scripts["mow_lawn"]["sequence"]))
        self.assertFalse(any(a[0] == "input_datetime.set_datetime" for a in runner.actions))
        self.assertEqual(runner.states("input_datetime.lawn_1_last_mow_1"), "2030-05-01 10:00:00")
        self.assertEqual(runner.states("input_text.mow_request"), "")

    def test_missing_and_unavailable_buttons_do_not_dispatch(self):
        for value in (None, "unavailable"):
            values = self.ready()
            if value is None: values.pop("button.mower_lawn_1")
            else: values["button.mower_lawn_1"] = value
            runner = Runner(values)
            runner.run(self.scripts["mow_lawn"]["sequence"])
            self.assertFalse(any(a[0] == "button.press" for a in runner.actions))

    def test_busy_paused_unknown_and_blocked_mowers_do_not_dispatch(self):
        for state in ("mowing", "returning", "paused", "unknown", "unavailable"):
            values = self.ready(); values["lawn_mower.mower"] = state
            runner = Runner(values); runner.run(self.scripts["mow_lawn"]["sequence"])
            self.assertEqual(runner.actions, [])
        for entity in ("input_boolean.do_not_mow", "binary_sensor.mowing_conditions_blocked"):
            values = self.ready(); values[entity] = "on"
            runner = Runner(values); runner.run(self.scripts["mow_lawn"]["sequence"])
            self.assertEqual(runner.actions, [])

    def test_one_dispatch_lock_and_retry_before_call(self):
        self.assertEqual(self.scripts["mow_lawn"]["mode"], "single")
        for i in range(1, 4):
            self.assertEqual(self.scripts[f"mow_lawn_{i}"]["sequence"][0]["action"], "script.mow_lawn")
            automation = next(a for a in self.files["automations.yaml"] if a["id"] == f"lawn_{i}_scheduler")
            self.assertEqual(automation["actions"][0]["action"], "input_datetime.set_datetime")
            self.assertIn("choose", automation["actions"][1])

    def test_recovery_preserves_future_and_never(self):
        values = {"input_boolean.mowing_automation_enabled":"on",
            "input_select.lawn_1_schedule":"once per week", "input_datetime.lawn_1_next_time":"2030-05-01 10:00:00",
            "input_select.lawn_2_schedule":"never", "input_datetime.lawn_2_next_time":"2030-05-01 10:00:00",
            "input_select.lawn_3_schedule":"twice per week", "input_datetime.lawn_3_next_time":"2030-06-01 10:00:00"}
        runner = Runner(values); runner.run(self.scripts["reconcile_mow_next_times"]["sequence"])
        self.assertEqual(len(runner.actions), 1)
        self.assertEqual(runner.states("input_datetime.lawn_1_next_time"), "2030-05-10 12:10:00")
        self.assertEqual(runner.states("input_datetime.lawn_3_next_time"), "2030-06-01 10:00:00")

    def test_rain_gate_and_missing_sensor_policy(self):
        sensor = next(b for t in self.templates for b in t.get("binary_sensor", []) if b["unique_id"] == "mowing_conditions_blocked")
        for enabled, rainfall, expected in (("off",None,False),("on",None,True),("on","0",False),("on","5",True)):
            values={"input_boolean.block_rain_mowing":enabled, "input_boolean.block_night_mowing":"off"}
            if rainfall is not None: values.update({"sensor.rain_today":rainfall,"sensor.rain_probability":"10"})
            env,_=environment(values)
            self.assertEqual(env.from_string(sensor["state"]).render(), expected)

    def test_session_records_only_real_activity_and_keeps_peak(self):
        sensor = self.logger()
        env,states=environment({"sensor.mower_progress":"20","sensor.mower_current_location":"Lawn 1", "lawn_mower.mower":"mowing"})
        previous={"active":{},"sessions":[]}
        active=render(env, sensor["attributes"]["active"], this={"attributes":previous},trigger={"id":"start"})
        self.assertEqual(active["lawn"],"Lawn 1")
        self.assertEqual(active["source"],"app")
        active["progress"]=100
        previous["active"]=active
        states.values["sensor.mower_progress"]="0"
        kept=render(env, sensor["attributes"]["active"], this={"attributes":previous},trigger={"id":"update"})
        self.assertEqual(kept["progress"],100)
        sessions=render(env, sensor["attributes"]["sessions"], this={"attributes":previous},trigger={"id":"end"})
        self.assertEqual(len(sessions),1)
        self.assertEqual(sessions[0]["outcome"],"completed")
        empty=render(env, sensor["attributes"]["sessions"], this={"attributes":{"active":{},"sessions":[]}},trigger={"id":"end"})
        self.assertEqual(empty,[])

    def test_request_attribution_expires(self):
        sensor = self.logger()
        for age, expected in ((30, "schedule"), (600, "app")):
            requested = (NOW - timedelta(seconds=age)).isoformat()
            env, _ = environment({"input_text.mow_request":"Lawn 2|schedule|" + requested,
                "sensor.mower_current_location":"Lawn 1", "sensor.mower_progress":"1"})
            active = render(env, sensor["attributes"]["active"], this={"attributes":{"active":{}}}, trigger={"id":"start"})
            self.assertEqual(active["source"], expected)
            self.assertEqual(active["lawn"], "Lawn 2" if age == 30 else "Lawn 1")

    def test_stale_errors_do_not_change_session_outcome(self):
        sensor = self.logger()
        active={"start":"2030-05-10T10:00:00+00:00","lawn":"Lawn 1","source":"app","progress":40,"error_code":""}
        for error_time, expected in (("2030-05-09T12:00:00+00:00", ""), ("2030-05-10T11:00:00+00:00", "123")):
            env, _=environment({"sensor.mower_last_error_code":"123","sensor.mower_last_error_time":error_time})
            result=render(env, sensor["attributes"]["active"], this={"attributes":{"active":active}}, trigger={"id":"update"})
            self.assertEqual(result["error_code"], expected)

    def test_session_resume_and_log_bound(self):
        sensor=self.logger(second=True)
        env,_=environment()
        active={"start":"2030-05-10T10:00:00+00:00","lawn":"Lawn 2","source":"app","progress":45,"error_code":""}
        previous={"active":active,"sessions":[{"outcome":"completed"}]*40}
        result=render(env, sensor["attributes"]["active"], this={"attributes":previous},trigger={"id":"start"})
        self.assertEqual(result["start"],active["start"])
        rows=render(env, sensor["attributes"]["sessions"], this={"attributes":previous},trigger={"id":"end"})
        self.assertEqual(len(rows),40)
        self.assertEqual(rows[0]["outcome"],"partial")
        self.assertEqual(rows[0]["mower"],"Mower 2")

    def test_public_files_have_no_installation_exports(self):
        forbidden = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9_.-]{20,}|\b(?:\d{1,3}\.){3}\d{1,3}\b|/(?:config|home)/[a-z][a-z0-9_-]+/|Luba-[A-Z0-9]{6,}|notify\.mobile_app_[a-z0-9_]+)")
        for path in ROOT.glob("*.yaml"):
            self.assertIsNone(forbidden.search(path.read_text()), path.name)
            if path.name.startswith("dashboard"):
                for line in path.read_text().splitlines():
                    self.assertFalse(re.match(r"\s*(?:latitude|longitude|x|y):\s*-?\d+\.\d+",line),path.name)
        self.assertFalse(any(ROOT.glob("*.png")))
        self.assertFalse((ROOT/".storage").exists())

if __name__ == "__main__":
    unittest.main()
