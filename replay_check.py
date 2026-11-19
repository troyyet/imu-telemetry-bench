# /// script
# requires-python = ">=3.11"
# dependencies = ["grpcio-tools==1.85.3", "protobuf==7.36.2"]
# ///
"""Run with 'uv run replay_check.py' in the same directory as imu_sample.proto."""

import io
import sys
from collections import deque
from pathlib import Path
from tempfile import TemporaryDirectory

from google.protobuf import proto
from grpc_tools import protoc


class ReplayInput(io.RawIOBase):
    """Expose at most one simulated USB read per readinto() call."""

    def __init__(self, chunks):
        self.chunks = deque(chunks)

    def readable(self):
        return True

    def readinto(self, target):
        if not self.chunks:
            return 0
        chunk = self.chunks.popleft()
        count = min(len(target), len(chunk))
        target[:count] = chunk[:count]
        if count < len(chunk):
            self.chunks.appendleft(chunk[count:])
        return count


def make_frame(sample_type, seq):
    sample = sample_type(seq=seq, sample_time_us=seq * 10_000)
    sample.specific_force_m_s2.z = 9.81
    sample.angular_rate_rad_s.SetInParent()  # Present, with zero rotation.
    wire = io.BytesIO()
    proto.serialize_length_prefixed(sample, wire)
    return wire.getvalue()


def main():
    schema = Path(__file__).resolve().with_name("imu_sample.proto")
    with TemporaryDirectory() as generated:
        result = protoc.main(["protoc", f"-I{schema.parent}",
                              f"--python_out={generated}", str(schema)])
        if result:
            raise SystemExit(result)
        sys.path.insert(0, generated)
        from imu_sample_pb2 import ImuSample

        frames = {seq: make_frame(ImuSample, seq) for seq in (41, 42, 43)}
        split = len(frames[43]) // 2
        # Drop frame 42. End the first read in the middle of frame 43.
        chunks = [frames[41] + frames[43][:split], frames[43][split:]]
        with io.BufferedReader(ReplayInput(chunks)) as stream:
            received = []
            while (sample := proto.parse_length_prefixed(ImuSample, stream)) is not None:
                assert sample.HasField("specific_force_m_s2")
                assert sample.HasField("angular_rate_rad_s")
                assert sample.sample_time_us == sample.seq * 10_000
                received.append(sample.seq)

        missing = [seq for a, b in zip(received, received[1:]) for seq in range(a + 1, b)]
        assert received == [41, 43] and missing == [42], (received, missing)
        print(f"decoded={received} missing={missing}")


if __name__ == "__main__":
    main()
