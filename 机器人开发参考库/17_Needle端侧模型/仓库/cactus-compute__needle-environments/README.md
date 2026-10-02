# needle-environments

Pre-configured environments for [Needle](https://github.com/cactus-compute/needle),
the 14 MB tool-calling model for tiny devices.

Each file is a standalone environment: a hand-curated set of tools whose
enums, bounds, and descriptions map cleanly onto Needle's constrained decoding,
a ready `needle.Needle` agent, and a test suite at the bottom.

| File | Surface |
|---|---|
| `smart_home.py` | Lights, thermostat, fans, blinds, robot vacuum |
| `media_player.py` | Smart speaker playback and volume |
| `productivity.py` | Timers, reminders, calendar, tasks, notes |
| `wearable.py` | Watch notifications, workouts, find-my-phone |
| `kitchen_appliance.py` | Oven, coffee maker, dishwasher, cooking timers |
| `data_capture.py` | Contacts, expenses, meals, water, weight |

## Use

```bash
pip install cactus-needle
python smart_home.py        # run the environment's frozen test suite
```

```python
import smart_home

smart_home.agent.complete("dim the study lights to 30 percent")
smart_home.run_tests()
```

To adapt an environment to your product, swap the `Literal` values (rooms,
contacts, categories) for your own and keep the shapes: closed sets as enums,
bounded numbers, verbatim copy for free text, five tools or fewer.
