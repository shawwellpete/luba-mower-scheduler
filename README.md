# Luba Mower Smart Scheduler for Home Assistant

**Version 2.1.0 · October 2026**

A rain-aware scheduler for Mammotion mowers using tasks saved in the Mammotion app. The core example controls one mower and three generic lawns. Optional dashboards add recent-session history, a lawn summary and a second mower's status/map.

- Per-lawn schedules with retry and recovery after a restart or a long pause.
- A confirmed mowing start before updating last-start history or advancing the weekly schedule.
- One shared dispatch lock so two lawns cannot issue competing starts.
- Separate manual, rain and night restrictions.
- Built-in-card dashboard, or optional custom dashboards with history in a popup.
- Maps without straight GPS-history joins; fixed-height activity/error cards.

The earlier [2026 scheduler write-up](https://peterblandford.com/blog/2026/06/02/luba-mower-home-assistant-scheduler-v2/) explains the move to saved-task buttons. See [CHANGELOG.md](CHANGELOG.md) for this update and [PRIVACY.md](PRIVACY.md) for publication checks.

## Requirements

- [Mammotion-HA](https://github.com/mikey0000/Mammotion-HA), with a saved-task button for each lawn. The examples follow the integration's 0.6.x service/entity model; confirm the entity names in your installation.
- Home Assistant's `sun` integration for the optional night restriction.
- Rainfall in mm and rain probability in percent if you enable the rain restriction.
- Optional custom dashboards: [Mushroom](https://github.com/piitaya/lovelace-mushroom), [button-card](https://github.com/custom-cards/button-card), [card-mod](https://github.com/thomasloven/lovelace-card-mod), [Browser Mod](https://github.com/thomasloven/hass-browser_mod), [map-card](https://github.com/nathan-gs/ha-map-card) and Mammotion's `ha-mammotion-assets` GeoJSON plugin. The normal `dashboard.yaml` needs no custom cards.

## Configure the saved tasks first

Create a task for each lawn in the Mammotion app, including its cutting angle, speed, blade height and edge settings. Synchronize schedules in the HA integration. Identify the buttons that **start those saved tasks**; area-enable switches are different entities and must not be substituted for task buttons.

The public examples use these placeholders:

| Purpose | Example |
|---|---|
| Mower | `lawn_mower.mower` |
| Saved lawn tasks | `button.mower_lawn_1`, `button.mower_lawn_2`, `button.mower_lawn_3` |
| Restore saved-task entities | `button.mower_synchronize_schedules` |
| GPS tracker | `device_tracker.mower` |
| Optional camera | `camera.mower` |
| Status sensors | `sensor.mower_battery`, `sensor.mower_progress`, `sensor.mower_elapsed_time`, `sensor.mower_current_location` |
| Optional error sensors | `sensor.mower_last_error`, `sensor.mower_last_error_code`, `sensor.mower_last_error_time` |

The `mower_last_lawn`, `mowing_session_log`, `mowing_conditions_blocked`, `mowing_block_reason` and `mower_task_buttons_blocked` entities are created by this project. Do not replace them with unrelated integration sensors. For the two-mower dashboard, map the corresponding `mower_2` integration entities as well. Every supplied name is a placeholder, not a real device identifier.

## Installation

1. Back up your configuration. Merge the helpers, scripts, automations and templates into your existing files; do not overwrite unrelated configuration.
2. Replace the integration-entity placeholders **across every YAML file you use**. In `template.yaml`, update the generic lawn names or map the integration's `current_location` values to those names if you want app-started sessions grouped with scheduler-started sessions.
3. Add each include once, or merge with your existing include arrangement:

   ```yaml
   input_boolean: !include input_boolean.yaml
   input_select: !include input_select.yaml
   input_datetime: !include input_datetime.yaml
   input_text: !include input_text.yaml
   template: !include template.yaml
   script: !include scripts.yaml
   automation: !include automations.yaml
   ```

   `template.yaml` and `automations.yaml` are lists; the helper and script files are mappings. If using `!include_dir_merge_list templates/`, put the template list in that directory instead of adding a second `template:` key.
4. Check the configuration, then reload the affected domains or restart HA. Confirm the expected entities exist before enabling scheduling.
5. Add **one** dashboard example as a view under `views:` in a dashboard's raw configuration:
   - `dashboard.yaml`: built-in cards, one mower.
   - `dashboard-advanced.yaml`: one mower, custom cards and popup history.
   - `dashboard-two-mowers.yaml`: two aligned mower status/maps with shared popup history.
6. Select each lawn's frequency and set its next mow. Turn on **Mowing Automation Enabled**. Leave unused lawns at `never` and remove their buttons from the task-availability template if those tasks do not exist.
7. To enable rain restrictions, first supply `sensor.rain_today` and `sensor.rain_probability` from your weather integration, then turn on **Block Rain Mowing**. Missing or nonnumeric rain data blocks mowing while that switch is on. With it off, rain sensors are optional.

Use your Home Assistant timezone. The dashboard formats session dates using that same timezone; no home coordinates are configured in the example maps.

## Upgrading from the June example

Keep your existing helper values and entity names. Replace the old script/automation definitions with the matching new definitions rather than running both versions.

Disable these retired automations if they remain in another file: `do_not_mow_if_rain`, `reset_do_not_mow_if_dry`, `block_mowing_at_night`, `allow_mowing_at_sunrise`. Weather/night rules now come from `binary_sensor.mowing_conditions_blocked`. `input_boolean.do_not_mow` is now a **manual block** which weather automations cannot clear. If an old automation left it on, clear it yourself only when you want mowing permitted. The old `reason_no_mow` helper is retained for compatibility but is no longer automatically updated.

Schedule selects no longer specify `initial: never`, so they restore your choices after restart. Their first-install default is still `never`. The original last-mow datetime helpers retain their IDs and now represent **confirmed starts**, not proof of a completed lawn.

## Scheduling and safeguards

An enabled lawn's due-time automation puts an hourly retry in place **before** attempting dispatch. The shared script only starts from `docked` or `idle`, with manual and weather/night restrictions clear. It checks that the selected task button exists and is available. An existing button whose state is `unknown` is allowed: buttons often have that state before their first press.

The script waits up to six minutes for the mower to report `mowing`. Only then does it update last-start history and schedule the next interval: seven days for weekly, three days for twice-weekly. A failure leaves history unchanged and displays a persistent notification. Manual buttons use the same guards; they do not override weather or start a new task on a paused mower.

On startup, re-enabling scheduling, frequency changes and every 15 minutes, overdue next-times are moved to future staggered slots. Future user-set times are preserved, and `never` schedules stay inactive. The dashboard's **Recover overdue schedules** button runs the same check. Changing a frequency affects the interval after the next confirmed start; it does not move an already-future start time.

The night restriction covers darkness plus a one-hour daylight margin. The template estimates the morning margin from the next sunrise; use dedicated sunrise/sunset helpers if exact margins across seasonal clock changes are important for your installation. Rain blocks above 3 mm or 50% probability. These are example thresholds: adjust them for your lawn and sensors.

Missing saved-task buttons are debounced for two minutes while the mower is idle/docked. The watchdog attempts one schedule synchronization, then reports any remaining problem. It does not repeatedly synchronize while the mower is working, when task buttons can temporarily disappear.

## History and dashboard behaviour

The template sensor records a session from an observed `mowing` start until the mower has been docked for one minute. Pauses retain the active session. A recharge that reaches stable dock ends a segment; resuming after that begins another segment. The last 40 segments per mower survive restart as restored trigger-sensor attributes.

Completion means the maximum observed progress reached at least 99%; otherwise a segment is partial, or an error if a timestamped error occurred during it. **Duration is session wall time and can include pauses**, not measured blade-running time. These records do not rewrite the lawn's last-start helpers or prove that an entire multi-charge job finished. An app-started session uses the integration's reported current location when known, otherwise `Unassigned`; GPS proximity never assigns a completed mow.

The larger **Mowing history** button shows the last observed lawn for each displayed mower. It opens the recent seven-day list and lawn summary. Full history retains source, progress and error details. Lawn-name grouping ignores capitalisation. Counts cover the available rolling log, so a busy mower can have fewer than 30 days retained.

Activity/error cards have the same 112px height, with scrolling for longer messages. Grey GPS-history lines are disabled independently of Mammotion's mowing overlay.

### Mowing coverage and Luba 3

A GPS tracker trail is not mowing coverage: straight joins can span missing location reports. Hiding those lines does not enable or disable the Mammotion coverage layer.

For cloud-connected mowers, **Enable mow path fetching (cloud)** in the Mammotion integration options permits downloading route data. This can increase cloud requests. Luba 2 covered-route data and Luba 3 dynamics-line data are different: a Luba 3 may only return a short yellow live trail and no full covered route. These dashboards do **not** fix that integration/firmware limitation and do not draw invented coverage from a progress percentage.

### Two mowers

`dashboard-two-mowers.yaml` and the second session sensor support monitoring two mowers. The bundled scheduler still dispatches **one mower**. The second logger classifies externally started work as `app`; an optional `input_text.mow_request_2` containing `Lawn name|schedule|ISO-8601 request time` can attribute a separately configured second scheduler.

To schedule a second mower, make a separate set of dispatch scripts, helpers and per-zone schedulers with its own shared dispatch lock, or build an assigned-mower scheduler. Do not point two mowers at the same dispatch helpers. Remove the second trigger sensor and last-lawn template if you only want a single-mower installation; missing second-mower entities otherwise leave those sensors empty.

## Validation

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
node tests/check_dashboard.cjs
```

The checks exercise dispatch/retry invariants, session handling, template rendering, placeholder references, dashboard JavaScript and publication hygiene. Also run Home Assistant's configuration check in your own installation before enabling the scheduler; placeholder devices cannot be tested against your mower by this repository.

## Credits

Built on [Mammotion-HA](https://github.com/mikey0000/Mammotion-HA) by Michael Arthur and the community. This is an example Home Assistant configuration, not an official Mammotion product.
