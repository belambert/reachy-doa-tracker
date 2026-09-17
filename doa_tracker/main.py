import threading
from reachy_mini import ReachyMini, ReachyMiniApp
# from reachy_mini.utils import create_head_pose
import numpy as np
import time
import requests
# from pydantic import BaseModel


class DoaTracker(ReachyMiniApp):
    # Optional: URL to a custom configuration page for the app
    # eg. "http://localhost:8042"
    custom_app_url: str | None = "http://0.0.0.0:8042"
    # Optional: specify a media backend ("gstreamer", "gstreamer_no_video", "default", etc.)
    # On the wireless, use gstreamer_no_video to optimise CPU usage if the app does not use video streaming
    request_media_backend: str | None = None

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        # App runs on the robot, so the daemon is local
        url = "http://localhost:8000/api/state/doa"
        session = requests.Session()
        last_doa, THRESHOLD = -1.0, 0.004

        while not stop_event.is_set():
            try:
                d = session.get(url, timeout=3.0).json()
            except requests.RequestException:
                time.sleep(0.5)
                continue

            if not d or not d["speech_detected"]:
                time.sleep(0.2)
                continue

            angle = d["angle"]
            if abs(angle - last_doa) > THRESHOLD:
                p_head = np.array([np.sin(angle), np.cos(angle), 0.0])
                R = reachy_mini.get_current_head_pose()[:3, :3]
                p = R @ p_head
                reachy_mini.look_at_world(p[0], p[1], p[2], duration=0.5)
                last_doa = angle
                time.sleep(0.6)   # let the move finish; motor noise skews DoA
            else:
                time.sleep(0.2)



if __name__ == "__main__":
    app = DoaTracker()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()