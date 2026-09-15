"""
logger.py
=========
Menyimpan setiap data yang diterima ke file CSV.
Satu file CSV baru dibuat untuk setiap jam, contoh:

    data/2026-09-11_15.csv
    data/2026-09-11_16.csv

Dipanggil otomatis oleh receiver.py setiap ada data baru masuk.
Tidak perlu dijalankan manual.
"""

import csv
import os
import time

import config

_HEADER = ["timestamp", "box_id", "salinitas", "air_temp", "water_temp", "humidity", "water_level"]


def _ensure_data_dir():
    os.makedirs(config.DATA_DIR, exist_ok=True)


def _current_filepath(epoch_time):
    _ensure_data_dir()
    filename = time.strftime("%Y-%m-%d_%H.csv", time.localtime(epoch_time))
    return os.path.join(config.DATA_DIR, filename)


def log_reading(box_id, values, epoch_time):
    """
    Simpan satu baris data ke CSV.
    values = {"salinitas":.., "air_temp":.., "water_temp":.., "humidity":.., "water_level":..}
    """
    filepath = _current_filepath(epoch_time)
    is_new_file = not os.path.exists(filepath)

    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time))

    try:
        with open(filepath, mode="a", newline="") as f:
            writer = csv.writer(f)
            if is_new_file:
                writer.writerow(_HEADER)
            writer.writerow([
                timestamp_str,
                box_id,
                values["salinitas"],
                values["air_temp"],
                values["water_temp"],
                values["humidity"],
                values["water_level"],
            ])
    except OSError as e:
        print(f"[logger] Gagal menulis CSV: {e}")
