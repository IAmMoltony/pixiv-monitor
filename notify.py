import subprocess
import dbus
import dbus.mainloop.glib
import logging
import webbrowser
from gi.repository import GLib

# i suck have used an external library for this but they all suck bcus "cross platform"
# probably gonna rewrite this a bit to work on windows + cross platform with fancy features

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

def send_notification(message, link):
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

        notification_id = interface.Notify("pixiv-monitor", 0, "printer", "pixiv-monitor alert!", message, actions, hints, 5000) # printer icon chosen for no reason

        def on_action_invoked(iden, action):
            print(f"got action on id {iden} action {action}")
            if iden == notification_id and action == "default":
                webbrowser.open(link)

        bus.add_signal_receiver(
            on_action_invoked,
            dbus_interface="org.freedesktop.Notifications",
            signal_name="ActionInvoked"
        )

        loop = GLib.MainLoop()
        loop.run()
    except Exception as exc:
        # we can't dbus let's try notify-send
        logging.getLogger().warn(f"Unable to send dbus notification: {exc}; trying notify-send instead")
        subprocess.run(["notify-send", "-i", "dialog-information", "pixiv-monitor alert!", message, "-t", "0"])
