# luba-mower-scheduler
(https://peterblandford.com/blog/2025/04/19/fully-automated-scheduler-for-my-luba-mower-in-home-assistant/)

# Luba Mower Smart Scheduler for Home Assistant

This project shows how to build a **fully automated, rain-aware mowing scheduler** for the Mammotion Luba robot mower using Home Assistant.

✅ Control when your mower starts  
✅ Set how many times per week to mow  
✅ Automatically delay mowing if rain is detected or forecast  
✅ Retry automatically until conditions are right  
✅ Full integration into your Home Assistant dashboard!

---

## ✨ Features

- Choose the first mow time of the week
- Set how many mows per week (e.g., 1 or 2 times)
- Delay mowing if rain is expected or it has rained recently
- Retry automatically every hour if conditions are bad
- Dashboard buttons to adjust settings easily
- Mower GPS tracking on a custom satellite map

---

## 🔗 Related Blog Post

Full explanation and setup guide here:  
➡️ [Fully Automated Scheduler for My Luba Mower in Home Assistant](https://peterblandford.com/blog/2025/04/19/fully-automated-scheduler-for-my-luba-mower-in-home-assistant/)

---

## 🛠 Integrations and Custom Cards Used

- [Mammotion Home Assistant Integration](https://github.com/mikey0000/Mammotion-HA)
- [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
- [Browser Mod](https://github.com/thomasloven/hass-browser_mod)
- [Map Card](https://github.com/nathan-gs/ha-map-card)
- [Lawn Mower Card](https://github.com/cociweb/lawn-mower-card)
- [Met Office Integration](https://www.home-assistant.io/integrations/metoffice)
- [OpenWeatherMap History](https://github.com/petergridge/openweathermaphistory)

---

## 📂 What's Included

- `automations.yaml` — Smart scheduler and rain-delay automations
- `dashboard.yaml` — Lovelace dashboard and Mushroom card layouts
- `input_boolean.yaml` — Input booleans for controlling zones and conditions
- `input_datetime.yaml` — Input datetimes for setting mow start times
- `input_select.yaml` — Input selects for choosing mow schedules (once/twice per week)
- `input_text.yaml` — Input texts for logging last mow, reason for delay, etc.
- `scripts.yaml` — Scripts to start, stop, and control mower tasks

---

## 📋 Notes

- Requires Home Assistant 2023.5+ recommended
- Designed for Mammotion Luba, but easily adaptable to other robot mowers
- Feel free to fork or modify!

---

## 📢 Credits

Special thanks to **Michael Arthur** for the original [Mammotion Home Assistant Integration](https://github.com/mikey0000/Mammotion-HA).

---
