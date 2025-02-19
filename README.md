# pixiv-monitor

pixiv-monitor is a Python script for monitoring Pixiv artist galleries, so you can stay up-to-date on your favorite anime pictures.

It even has RSS support. It's pretty basic, but works.

## Installing

1. Make sure you have Python 3 on your computer
2. Clone the repository
3. Install the dependencies: `pip install -r requirements.txt`
4. Done

Before running the script (`main.py`), you'll need to configure it as described below.

## Configuring

Before using pixiv-monitor, you have to configure it.

First copy `settings-example.json` as `settings.json`. In the `settings.json` file, you'll need to set a few options:

1. `access_token` and `refresh_token`: Your Pixiv API tokens.
1. `artist_ids`: A list of IDs of the artists whose galleries you want to monitor.
1. `check_interval`: How often to check, in seconds.
1. `notifications_off`: Enable this option to disable system notifications.
1. `num_threads`: Number of threads to use to check for artists. More threads speeds up the process, especially if you monitor many artists. Make sure you don't set it too high **or the script (and possibly your system) might break.**
1. `email`: Whether to enable email notifications.

### SMTP options

These are entirely optional if you don't want to use email notifications.

1. `mail_host`: The SMTP host server. `address` is the SMTP host address, `port` is the port.
1. `from_address`: What address the emails will be sent from.
1. `to_address`: What address the emails will be sent to.
4. `credentials`: Your login and password for the email host server.

## RSS

To add RSS, simply run `rssmain.py` alongside `main.py`. It will automatically create the RSS file (`pixiv.atom`), which can then either be accessed locally or served using an HTTP server.
