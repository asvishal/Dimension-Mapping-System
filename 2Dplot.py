import time
import numpy as np
import serial
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtWidgets

# --- Serial Setup ---
ser = serial.Serial('COM5', 9600)  # Change this to your port
time.sleep(2)

# --- GUI Setup ---
app = QtWidgets.QApplication([])
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('Real-Time 2D Object Scan (Y-Z)')
w.setCameraPosition(distance=5)

# --- Grid & Scatter Plot ---
grid = gl.GLGridItem()
w.addItem(grid)

# --- Add XYZ Axes ---
# X-axis (Red)
x_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [2, 0, 0]]), color=(1, 0, 0, 1), width=2, antialias=True)
w.addItem(x_axis)

# Y-axis (Green)
y_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 2, 0]]), color=(0, 1, 0, 1), width=2, antialias=True)
w.addItem(y_axis)

# Z-axis (Blue)
z_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 0, 2]]), color=(0, 0, 1, 1), width=2, antialias=True)
w.addItem(z_axis)

# --- Point Cloud ---
points = np.empty((0, 3))
object_points = []
max_object_distance = 50  # in cm

scatter = gl.GLScatterPlotItem(pos=points, color=(0, 1, 0, 1), size=6)
w.addItem(scatter)

# --- Update Function ---
def update():
    global points, object_points
    if ser.in_waiting:
        try:
            line = ser.readline().decode(errors='ignore').strip()
            if line.startswith("Point:"):
                parts = line.replace("Point:", "").split()
                if len(parts) == 3:
                    x_str, y_str, z_str = parts
                    x = float(x_str.split('=')[1])
                    y = float(y_str.split('=')[1])
                    z = float(z_str.split('=')[1])

                    distance = np.linalg.norm([x, y, z])
                    if distance <= max_object_distance:
                        new_point = np.array([[y, z, 0]])  # Y-Z plane, ignore X for plotting
                        points = np.vstack([points, new_point])
                        object_points.append([y, z])
                        scatter.setData(pos=points)
                else:
                    print("Invalid line format:", line)
        except Exception as e:
            print("Error:", e)

# --- Timer ---
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(30)

# --- Save on Key Press ---
def keyPressEvent(event):
    global object_points, points
    if event.key() == QtCore.Qt.Key_S:
        label = input("Enter object label: ")
        filename = f"object_{label}_{int(time.time())}"

        object_points_np = np.array(object_points)
        np.savetxt(f"{filename}.csv", object_points_np, delimiter=",", header="Y,Z", comments='')
        print(f"✅ Saved {len(object_points)} points as {filename}.csv")

        img = w.grabFramebuffer()
        img.save(f"{filename}.png")
        print(f"🖼️ Saved graph as {filename}.png")

        object_points = []
        points = np.empty((0, 3))
        scatter.setData(pos=points)

w.keyPressEvent = keyPressEvent
app.exec_()
