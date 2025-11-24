import socket
import json
import time
import pandas as pd
import numpy as np
import os
import datetime

# -----------------------------------------------------------
# Resolve Parquet directory (portable for Docker)
# -----------------------------------------------------------
PARQUET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "sample", "parquet_delay_and_weather_25"
)

print("Reading parquet from:", PARQUET_DIR)

class EnhancedJSONEncoder(json.JSONEncoder):
    """Robust JSON encoder that handles datetime, numpy, and pandas objects safely."""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, pd.Timestamp)):
            return obj.isoformat()
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.str_, np.bytes_)):
            return str(obj)
        elif obj is None or (isinstance(obj, float) and np.isnan(obj)):
            return None
        elif isinstance(obj, (np.ndarray, list, tuple)):
            return [self.default(x) for x in obj]
        else:
            try:
                return str(obj)
            except Exception:
                return super().default(obj)

def load_parquet_data(path):
    if os.path.isdir(path):
        print(f"Reading all Parquet files in directory: {path}")
        df = pd.read_parquet(path)
    else:
        df = pd.read_parquet(path)

    df = df.copy()

    df["DepTime"] = df["DepTime"].fillna(0).astype(int).astype(str).str.zfill(4)
    df["DepDatetime"] = pd.to_datetime(
        df["FlightDate"].astype(str) + " " +
        df["DepTime"].str.slice(0, 2) + ":" + df["DepTime"].str.slice(2, 4),
        errors="coerce"
    )

    df = df.sort_values("DepDatetime").reset_index(drop=True)
    return df

def start_streaming(path, host="localhost", port=9998, delay=5.0):
    df = load_parquet_data(path)
    print(f"Loaded {len(df)} rows from {path}")

    df["window_start"] = df["DepDatetime"].dt.floor("5min")
    windows = df.groupby("window_start")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Streaming flight data (5-min batches) to {host}:{port}...")

    while True:
        try:
            conn, addr = server_socket.accept()
            print(f"New client connected: {addr}")

            for window_start, batch in windows:
                try:
                    records = batch.to_dict(orient="records")
                    payload = {
                        "window_start": str(window_start),
                        "num_records": len(records),
                        "records": records,
                    }

                    conn.send((json.dumps(payload, cls=EnhancedJSONEncoder) + "\n").encode("utf-8"))
                    print(f"Sent {len(records)} records for window starting {window_start}")
                    time.sleep(delay)

                except (BrokenPipeError, ConnectionResetError):
                    print(f"Client {addr} disconnected. Waiting for a new client.")
                    break

        except Exception as e:
            print(f"Error accepting connection: {e}")
            time.sleep(1)

if __name__ == "__main__":
    start_streaming(PARQUET_DIR)
