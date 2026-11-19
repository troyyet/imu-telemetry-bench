# IMU telemetry bench

A Protobuf telemetry contract and a runnable USB-stream replay check for a planned Raspberry Pi Pico (RP2040) and Bosch BMI270 bench setup.

The current implementation contains the message schema and a synthetic replay check. Firmware, a live serial recorder, and physical measurements are planned work. Hardware acceptance remains pending.

Run the check with Python 3.11 or later and [uv](https://docs.astral.sh/uv/).

```sh
uv run --script replay_check.py
```

Expected output

```text
decoded=[41, 43] missing=[42]
```

The script compiles `imu_sample.proto`, constructs three length-prefixed Protobuf samples, drops sample 42, and splits sample 43 between simulated USB reads. A buffered reader reassembles the payloads. The check verifies the decoded samples, acquisition timestamps, presence of both vectors, and the missing sequence number.

Each frame contains a Protobuf varint byte count followed by one `telemetry.v1.ImuSample`. Acceleration is specific force in m/s^2. Angular rate is in rad/s. Both vectors use the sensor package axes. Sequence numbers and acquisition time reset on boot.

The planned sensor link is 4-wire SPI from a [Bosch BMI270](https://www.bosch-sensortec.com/products/motion-sensors/imus/bmi270/) to a [Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/). Firmware will stream samples over USB CDC ACM to a Python recorder.

The first implementation milestone is a live `capture` command that writes the same messages to CSV and detects missing samples. Later milestones cover the BMI270 firmware and stationary gyro-offset calibration. Physical validation will include flipping the stationary sensor to check the sign of the Z acceleration reading.

The intended Devin Bot workflow uses repository issues to track a failing capture through reproduction, a coding session, CI, and PR review. I will own flashing the board, bench measurements, and merge approval. The Bot integration is planned.
