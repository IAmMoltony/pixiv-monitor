# pixiv-monitor

pixiv-monitor is a Python script for monitoring Pixiv artist galleries, so you can stay up-to-date on your favorite anime pictures.

It supports RSS and sending notifications using ntfy.

## Installing

1. Make sure you have Python 3 on your computer
2. Clone the repository
3. Install the dependencies: `pip install -r requirements.txt`
4. Done

If you're on Windows, it's recommended to run the script in a terminal that supports ANSI escape sequences,
such as Windows Terminal.

Before running the script (`main.py`), you'll need to configure it as described below.

## Configuring

Before using pixiv-monitor, you have to configure it.

First copy `settings-example.json` as `settings.json`. In the `settings.json` file, you'll need to set a few options:

1. `artist_ids`: A list of IDs of the artists whose galleries you want to monitor.
1. `check_interval`: How often to check, in seconds.
1. `notifications_off`: Enable this option to disable system notifications.
1. `num_threads`: Number of threads to use to check for artists. More threads speeds up the process, especially if you monitor many artists. Make sure you don't set it too high **or the script (and possibly your system) might break.**
1. `log`: Options for logging described below.
1. `ntfy_topic`: Topic in which to send notifications using `ntfy.sh`. Skip this option if you don't need `ntfy.sh` notifications.

### Logging options

1. `backup_count`: How many log files to keep.
1. `max_size`: Maximum size of one log file in MiB.
1. `directory`: What directory to keep log files in.

## Authentication

It's best to create a separate Pixiv account if you want to use the site in the browser without hitting a rate limit.

Copy `.env.example` as `.env` and set the `REFRESH_TOKEN` variable. This is your Pixiv refresh token.

The `.env` file should now look like this:

```
REFRESH_TOKEN='your-refresh-token'
```

## System notifications

To get system notifications to work, you'll need to install some stuff depending on your OS.

### Linux

You'll need to install the python dbus package. Commands for the most common distros:

```bash
sudo apt install -y python3-dbus # debian and ubuntu
sudo dnf install -y python3-dbus # fedora red hat
sudo pacman -S python-dbus # arch btw
sudo zypper install python3-dbus # opensuse (option 1)
sudo zypper install dbus-1-python # opensuse (option 2)
```

If nothing works, you can try using the pip package:

```bash
pip install dbus-python
```

### Windows

Install `winotify`:

```bash
pip install winotify
```

notifications will work now

and yeah it only works on windows 10+ but lowkey you shouldn't be using anything older if ur on windows

## RSS

To add RSS, simply run `rssmain.py` alongside `main.py`. It will automatically create the RSS file (`pixiv.atom`), which can then either be accessed locally or served using an HTTP server.
