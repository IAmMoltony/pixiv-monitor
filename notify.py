import subprocess
import logging
import webbrowser
import threading
import sys
import requests

# lunix
try:
    import dbus
    import dbus.mainloop.glib
    from gi.repository import GLib
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
except ImportError:
    dbus = None

# window
try:
    import winotify
except ImportError:
    winotify = None

# i could have used an external library for this but they all suck bcus "cross platform"

def r18_title_prefix(r18_tag):
    return f"[!{r18_tag}!]" if len(r18_tag) > 0 else ""

def send_notification(message, link, r18_tag=""):
    title_prefix = r18_title_prefix(r18_tag)
    if sys.platform.startswith("linux"):
        if dbus:
            try:
                # try dbusing it first
                bus = dbus.SessionBus()
                notifications = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
                interface = dbus.Interface(notifications, "org.freedesktop.Notifications")

                hints = {
                    "resident": dbus.Boolean(True),
                    "urgency": dbus.Byte(2) # the highest one. you wanna be the first to view those pics right
                }

                actions = ["default", "View"]

                notification_id = interface.Notify("pixiv-monitor", 0, "printer", f"{title_prefix}pixiv-monitor alert!", message, actions, hints, 0) # printer icon chosen for no reason

                def on_action_invoked(iden, action):
                    if iden == notification_id and action == "default":
                        webbrowser.open(link)
                        interface.CloseNotification(notification_id)
                        loop.quit()

                bus.add_signal_receiver(
                    on_action_invoked,
                    dbus_interface="org.freedesktop.Notifications",
                    signal_name="ActionInvoked"
                )

                def run_loop():
                    global loop
                    loop = GLib.MainLoop()
                    loop.run()

                threading.Thread(target=run_loop, daemon=True).start()
                return
            except Exception as exc:
                logging.getLogger().warn(f"Unable to send dbus notification: {exc}; trying notify-send instead")

        # fallback in case we don't have dbus or it fail
        subprocess.run(["notify-send", "-i", "dialog-information", f"{title_prefix}pixiv-monitor alert!", message, "-t", "0"])
    elif sys.platform.startswith("win"):
        if winotify:
            toast = winotify.Notification(app_id="pixiv-monitor", title=f"{title_prefix}pixiv-monitor alert!", msg=message)
            toast.add_actions(label="View", launch=link)
            toast.show()

def send_ntfy(ntfy_topic, message, link, r18_tag=""):
    title_prefix = r18_title_prefix(r18_tag)
    requests.post(
        f"https://ntfy.sh",
        json={
            "topic": ntfy_topic,
            "title": f"{title_prefix}pixiv-monitor alert!",
            "message": message,
            "click": link
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
