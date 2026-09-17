import threading
from reachy_mini import ReachyMini, ReachyMiniApp
# from reachy_mini.utils import create_head_pose
import numpy as np
import time
import requests


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

            # So 0 means left, π/2 means straight ahead and π means right.
            doa = d["angle"]
            if abs(doa - last_doa) > THRESHOLD:
                print(f"doa: {fmt_doa(doa)}")
                body_yaw = reachy_mini.get_current_joint_positions()[0][0]
                print(f"body yaw: {np.degrees(body_yaw):.0f}°")
                dir_head = np.array([np.sin(doa), np.cos(doa), 0.0])
                print(f"dir (head frame): {dir_head}")
                head_rot = reachy_mini.get_current_head_pose()[:3, :3]
                print(f"head rotation:\n{head_rot}")
                dir_world = head_rot @ dir_head
                print(f"dir (world frame): {dir_world}")
                reachy_mini.look_at_world(*dir_world, duration=1.0)
                last_doa = doa
                time.sleep(0.6)   # let the move finish; motor noise skews DoA
            else:
                time.sleep(0.2)


def fmt_doa(angle: float) -> str:
    """Format a DoA angle (0 = left, π/2 = front, π = right) as degrees off center."""
    deg = np.degrees(angle) - 90
    side = "L" if deg < 0 else "R" if deg > 0 else ""
    return f"{abs(deg):.0f}° {side}".strip()


if __name__ == "__main__":
    app = DoaTracker()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()