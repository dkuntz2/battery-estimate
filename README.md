# battery estimate

because the gnome-shell estimator is just not good.

this script has no external dependencies, other than that you be running linux, preferably on a laptop (i haven't actually tested it when there are no batteries present, so who knows how that'll work).

the things it looks at are `/sys/class/power_supply/BAT*/`:

- `status` - to determine if the battery is charging, discharging, or not in use
- `energy_now` - to find out how much power the battery currently has
- `energy_full` - to find out what the charge capacity of the battery is
- `power_now` - to find out what the current power draw is
- `charge_stop_threshold` - to see if you're limiting how full a battery can be before it stops charging

at some point i could probably turn this into a small library (and might, because it's something i definitely personally want to use for more than just one script).
but for now it's just a tiny script which tells you basic information.
