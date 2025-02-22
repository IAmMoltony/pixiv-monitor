import subprocess
import logging
import webbrowser
import threading
import sys

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
    import win10toast_click
except ImportError:
    win10toast_click = None

# i could have used an external library for this but they all suck bcus "cross platform"
# probably gonna rewrite this a bit to work on windows + cross platform with fancy features

def send_notification(message, link):
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

                notification_id = interface.Notify("pixiv-monitor", 0, "printer", "pixiv-monitor alert!", message, actions, hints, 0) # printer icon chosen for no reason

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
        subprocess.run(["notify-send", "-i", "dialog-information", "pixiv-monitor alert!", message, "-t", "0"])
    elif sys.platform.startswith("win"):
        if win10toast_click:
            def do_notification():
                def open_link():
                    webbrowser.open(link) # TODO handle the stupid ass warning that wparam or some shit im not familiar with win32
                win10toast_click.ToastNotifier().show_toast("pixiv-monitor alert!", message, duration=10, callback_on_click=open_link)
            threading.Thread(target=do_notification, daemon=True).start()
        else:
            logging.getLogger().warn("Can't send notification because win10toast-click isn't installed")
