import random

class SimpleKalmanFilter:
    def __init__(self, process_variance, measurement_variance, initial_estimate=0.0):
        self.process_variance = process_variance      # Q: expected change in system
        self.measurement_variance = measurement_variance  # R: sensor noise
        self.estimate = initial_estimate              # x: initial state
        self.error_estimate = 1.0                     # P: estimate error

    def update(self, measurement):
        kalman_gain = self.error_estimate / (self.error_estimate + self.measurement_variance)
        self.estimate = self.estimate + kalman_gain * (measurement - self.estimate)
        self.error_estimate = (1 - kalman_gain) * self.error_estimate + self.process_variance
        return self.estimate

kf = SimpleKalmanFilter(process_variance=0.01, measurement_variance=0.1)

noisy_readings = [random.uniform(9.5, 10.5) for _ in range(20)]
smoothed = []

for reading in noisy_readings:
    filtered = kf.update(reading)
    smoothed.append(filtered)
    print(f"Noisy: {reading:.2f} -> Filtered: {filtered:.2f}")
