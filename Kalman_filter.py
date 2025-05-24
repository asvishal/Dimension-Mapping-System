import numpy as np
import serial
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtWidgets

class SimpleKalman:
    def __init__(self, process_variance=1e-3, measurement_variance=0.05):
        self.x = 0.0
        self.P = 1.0
        self.Q = process_variance
        self.R = measurement_variance

    def update(self, measurement):
        # Prediction update
        self.P += self.Q

        # Measurement update
        K = self.P / (self.P + self.R)
        self.x += K * (measurement - self.x)
        self.P *= (1 - K)
        return self.x

kalman_x = SimpleKalman()
kalman_y = SimpleKalman()
kalman_z = SimpleKalman()

ser = serial.Serial('COM5', 9600)
app = QtWidgets.QApplication([])
w = gl.GLViewWidget()
w.setWindowTitle('3D Point Cloud with Kalman & Boundary')
w.setCameraPosition(distance=20)
w.show()

grid = gl.GLGridItem()
w.addItem(grid)

points = np.empty((0, 3))
scatter = gl.GLScatterPlotItem(pos=points, color=(1, 1, 1, 1), size=5)
w.addItem(scatter)

boundary_box = gl.GLLinePlotItem(color=(1, 0, 0, 1), width=2, mode='line_strip')
w.addItem(boundary_box)

def draw_bounding_box(obj_points):
    obj_points = np.array(obj_points)
    min_corner = obj_points.min(axis=0)
    max_corner = obj_points.max(axis=0)

    x0, y0, z0 = min_corner
    x1, y1, z1 = max_corner

    corners = np.array([
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z0],  # Bottom face
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [x0, y0, z1],  # Top face
        [x0, y0, z0], [x0, y0, z1], [x1, y0, z0], [x1, y0, z1],
        [x1, y1, z0], [x1, y1, z1], [x0, y1, z0], [x0, y1, z1]
    ])
    boundary_box.setData(pos=corners)

def update():
    global points
    if ser.in_waiting:
        line = ser.readline().decode(errors='ignore').strip()
        if line.startswith("Point:"):
            try:
                parts = line.replace("Point:", "").split()
                x = float(parts[0].split('=')[1])
                y = float(parts[1].split('=')[1])
                z = float(parts[2].split('=')[1])

                # Kalman filtered
                x_f = kalman_x.update(x)
                y_f = kalman_y.update(y)
                z_f = kalman_z.update(z)

                point = np.array([[x_f, y_f, z_f]])
                points = np.vstack([points, point])
                if len(points) > 1000:
                    points = points[-1000:]
                scatter.setData(pos=points)

                draw_bounding_box(points)
            except Exception as e:
                print("Error:", e)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(30)

QtWidgets.QApplication.instance().exec_()
