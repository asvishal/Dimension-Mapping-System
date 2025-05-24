import time
import numpy as np
import serial
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtWidgets
from scipy.spatial import ConvexHull

# --- Serial Setup ---
ser = serial.Serial('COM5', 9600)
time.sleep(2)

# --- App Setup ---
app = QtWidgets.QApplication([])
w = gl.GLViewWidget()
w.setWindowTitle('3D Point Cloud with Bounding Box')
w.setCameraPosition(distance=30)
w.show()

# --- Grid ---
g = gl.GLGridItem()
w.addItem(g)

# --- Data Containers ---
points = np.empty((0, 3))
object_points = []
sp = gl.GLScatterPlotItem(pos=points, color=(1, 1, 1, 1), size=5)
w.addItem(sp)

# --- Bounding Box Lines ---
bbox_lines = []

def draw_bounding_box(pts):
    global bbox_lines
    for line in bbox_lines:
        w.removeItem(line)
    bbox_lines = []

    if len(pts) < 4:
        return

    try:
        hull = ConvexHull(pts)
        for simplex in hull.simplices:
            p1, p2 = pts[simplex]
            line = gl.GLLinePlotItem(pos=np.array([p1, p2]), color=(1, 0, 0, 1), width=2, mode='lines')
            w.addItem(line)
            bbox_lines.append(line)
    except Exception as e:
        print("Bounding box error:", e)

# --- Complementary Filter Setup ---
alpha = 0.98
pitch, roll = 0.0, 0.0
last_time = QtCore.QTime.currentTime()

# --- Moving Average Filter for Distance ---
ultrasonic_window = []
window_size = 5

def filter_ultrasonic(val):
    ultrasonic_window.append(val)
    if len(ultrasonic_window) > window_size:
        ultrasonic_window.pop(0)
    return np.mean(ultrasonic_window)

# --- Update Function ---
def update():
    global points, object_points, pitch, roll, last_time

    if ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("MPU:") and "Ultra:" in line:
                parts = line.split()

                ax = float(parts[1].split('=')[1])
                ay = float(parts[2].split('=')[1])
                az = float(parts[3].split('=')[1])
                gx = float(parts[4].split('=')[1])
                gy = float(parts[5].split('=')[1])
                dist = float(parts[7].split('=')[1])  # in meters

                now = QtCore.QTime.currentTime()
                dt = last_time.msecsTo(now) / 1000.0
                last_time = now

                # Complementary Filter
                acc_pitch = np.arctan2(ax, np.sqrt(ay ** 2 + az ** 2)) * 180 / np.pi
                acc_roll = np.arctan2(ay, np.sqrt(ax ** 2 + az ** 2)) * 180 / np.pi

                pitch = alpha * (pitch + gx * dt) + (1 - alpha) * acc_pitch
                roll = alpha * (roll + gy * dt) + (1 - alpha) * acc_roll

                dist_filtered = filter_ultrasonic(dist)

                if dist_filtered <= 0 or dist_filtered > 0.5:
                    return  # Ignore invalid or distant readings

                # Convert to 3D point
                z = dist_filtered
                x = np.sin(np.radians(roll)) * z
                y = np.sin(np.radians(pitch)) * z
                new_point = np.array([[x, y, z]])

                points = np.vstack((points, new_point))
                object_points.append(new_point[0])

                if len(points) > 1000:
                    points = points[-1000:]
                sp.setData(pos=points)

                draw_bounding_box(np.array(object_points))

        except Exception as e:
            print("⚠️ Error parsing:", e)

# --- Save Object (Optional) ---
def keyPressEvent(event):
    global points, object_points
    if event.key() == QtCore.Qt.Key_S:
        label = input("🔤 Label (box/sphere): ")
        timestamp = int(time.time())
        base = f"object_{label}_{timestamp}"

        np.savetxt(f"{base}.csv", np.array(object_points), delimiter=",")
        print(f"✅ Saved point cloud as {base}.csv")

        img = w.grabFramebuffer()
        img.save(f"{base}.png")
        print(f"🖼️ Snapshot saved as {base}.png")

        points = np.empty((0, 3))
        object_points = []
        sp.setData(pos=points)
        draw_bounding_box(points)

w.keyPressEvent = keyPressEvent

# --- Timer ---
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(30)

# --- Run App ---
app.exec_()
