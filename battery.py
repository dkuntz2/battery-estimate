from pathlib import Path
from datetime import timedelta
import math

class Battery():
    _PROPS = {
        "status": str,
        "energy_now": int,
        "power_now": int,
        "energy_full": int,
        "charge_start_threshold": int,
        "charge_stop_threshold": int,
    }

    @classmethod
    def all(cls):
        power_supply_path = Path("/sys/class/power_supply/")
        if not power_supply_path.exists():
            raise ValueError("No /sys/class/power_supply/ to derive information from")

        batteries = []
        for path in power_supply_path.glob("BAT*"):
            batteries.append(cls(path))

        return batteries

    def __init__(self, path):
        self.path = path
        self.name = self.path.name

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        if attr in self._PROPS:
            return self._PROPS[attr](self._read_file(attr))
        raise AttributeError(f"'{self.__class__}' has no attribute '{attr}'")

    def _read_file(self, name):
        fp = self.path / name
        with fp.open() as f:
            content = f.read().strip()

        return content

    def time_remaining(self):
        status = self.status
        if status.lower() != "discharging":
            return -1

        return self.energy_now / float(self.power_now)

    @property
    def energy_charge_threshold(self):
        percent = float(self._read_file("charge_stop_threshold")) / 100.0
        energy_stop_charge = self.energy_full * percent
        return energy_stop_charge



class Batteries():
    def __init__(self, batteries):
        self.batteries = sorted(batteries, key=lambda x: x.name)

        def sum_attr(attr):
            def summer():
                return sum([getattr(b, attr) for b in self.batteries])

            return summer

        self.energy_now = sum_attr("energy_now")
        self.power_now = sum_attr("power_now")
        self.energy_full = sum_attr("energy_full")
        self.energy_charge_threshold = sum_attr("energy_charge_threshold")

    def power_now_human(self):
        mw = self.power_now() / 1000
        w = mw / 1000.0
        return w

    def status(self):
        statuses = [b.status.lower() for b in self.batteries]
        if "charging" in statuses:
            return "charging"
        if "discharging" in statuses:
            return "discharging"
        return "ac power"

    def time_remaining(self):
        if self.status() != "discharging":
            return -1
        return self.energy_now() / float(self.power_now())

    def _humanize_time(self, hours):
        delta = timedelta(hours=hours)

        # remove microseconds
        delta -= timedelta(microseconds=delta.microseconds)

        # remove seconds - convert to nearest minute
        seconds = delta.seconds % 60
        if seconds > 30:
            delta += timedelta(seconds=(60-seconds))
        else:
            delta -= timedelta(seconds=seconds)

        minutes = int((delta.seconds / 60) % 60)
        hours = int(delta.seconds / 60 / 60)

        return f"{hours}:{minutes:02d}"

    def time_remaining_human(self):
        if self.time_remaining() == -1:
            return "not using battery"
        return self._humanize_time(self.time_remaining())


    def time_to_charge_human(self):
        if self.status() != "charging":
            return -1

        total_missing = 0
        for battery in self.batteries:
            total_missing += battery.energy_charge_threshold - battery.energy_now

        return self._humanize_time(total_missing / float(self.power_now()))

    def percent_trunc(self, num):
        return math.trunc(num * 10000) / 100.0

    def battery_percent(self):
        decimal = float(self.energy_now()) / float(self.energy_full())
        return self.percent_trunc(decimal)

    def all_battery_percents(self):
        percents = []
        for b in self.batteries:
            decimal = float(b.energy_now) / float(b.energy_full)
            percent = self.percent_trunc(decimal)
            percents.append(percent)

        return percents

    def battery_in_use(self):
        for b in self.batteries:
            if b.status.lower() in ["charging", "discharging"] :
                return b.name
        return "ac power"

    def power_now_human(self):
        raw_watts = self.power_now() / 1000.0 / 1000.0
        step = 100.0
        watts = math.trunc(raw_watts * step) / step
        return watts


    def hud(self):
        status_line = f"{self.status()} - "
        if len(self.batteries) > 1:
            status_line += f"batteries: {len(self.batteries)} - using {self.battery_in_use()} - "
        status_line += f"{self.battery_percent()}%"
        if len(self.batteries) > 1:
            percents = ", ".join([f"{str(p)}%" for p in self.all_battery_percents()])
            status_line += f" ({percents})"

        print(status_line)

        if self.status() == "discharging":
            print(f"\testimated battery remaining: {self.time_remaining_human()}")
            print(f"\tcurrent power draw: {self.power_now_human()} W")
        elif self.status() == "charging":
            print(f"\testimated charge time: {self.time_to_charge_human()}")
        else:
            print("\tusing ac power")

