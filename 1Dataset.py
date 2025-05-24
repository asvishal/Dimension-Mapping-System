import time
import numpy as np
import serial
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtWidgets, QtCore

ser = serial.Serial('COM5', 9600)  # Adjust as needed
time.sleep(2)

app = QtWidgets.QApplication([])
w = gl.GLViewWidget()
w.setWindowTitle('Real-Time 3D Point Cloud')
w.setCameraPosition(distance=30)
w.show()

grid = gl.GLGridItem()
w.addItem(grid)

points = np.empty((0, 3))
object_points = []

scatter = gl.GLScatterPlotItem(pos=points, color=(0, 1, 0, 1), size=5)
w.addItem(scatter)

def update():
    global points, object_points
    try:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("Point:"):
                parts = line.replace("Point:", "").split()
                x = float(parts[0].split("=")[1])
                y = float(parts[1].split("=")[1])
                z = float(parts[2].split("=")[1])

                new_point = np.array([[x, y, z]])
                distance = np.linalg.norm(new_point)

                if distance < 50:  # 50 cm = 0.5 m
                    points = np.vstack((points, new_point))
                    object_points.append(new_point[0])

                    if len(points) > 1000:
                        points = points[-1000:]
                    scatter.setData(pos=points)
    except Exception as e:
        print("⚠️ Error in update:", e)

def keyPressEvent(event):
    global points, object_points
    if event.key() == QtCore.Qt.Key_S:
        label = input("🔤 Enter object label (box/sphere/etc): ")
        timestamp = int(time.time())
        base_filename = f"object_{label}_{timestamp}"

        np.savetxt(f"{base_filename}.csv", np.array(object_points), delimiter=",")
        print(f"✅ Saved {len(object_points)} points to {base_filename}.csv")

        img = w.grabFramebuffer()
        img.save(f"{base_filename}.png")
        print(f"🖼️ Saved image to {base_filename}.png")

        # Reset for next object
        points = np.empty((0, 3))
        object_points = []
        scatter.setData(pos=points)

w.keyPressEvent = keyPressEvent

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(30)

app.exec_()
