"""
config.py
=========
Semua pengaturan sistem Box Monitor ada di sini.
Kalau ada perubahan pin, alamat radio, atau daftar box, cukup ubah di file ini
(file lain tidak perlu disentuh).
"""

import struct

# ======================================================
# NRF24L01 (WIRING KE RASPBERRY PI)
# ======================================================
CE_PIN = 25          # GPIO25 (BCM) -> kaki CE di modul NRF24
CSN_PIN = 0          # 0 = /dev/spidev0.0 (CE0), sesuai wiring CSN -> GPIO8/CE0

RADIO_ADDRESS = b"TUNL1"   # HARUS SAMA PERSIS dengan Arduino:
                           # const byte radioAddress[6] = "TUNL1";

RADIO_CHANNEL = 76         # Arduino tidak mengubah channel -> pakai default library (76)
DATA_RATE = "1MBPS"        # harus sama dengan Arduino: radio.setDataRate(RF24_1MBPS)
PA_LEVEL = "LOW"           # harus sama dengan Arduino: radio.setPALevel(RF24_PA_LOW)

# ======================================================
# FORMAT DATA
# Harus 100% sama dengan struct SensorData di file .ino:
#
#   struct SensorData {
#     char  box_id[8];
#     float waterTemperature;
#     float airTemperature;
#     float humidity;
#     int   waterLevel;   -> di Arduino (AVR) "int" ukurannya 2 byte
#     float salinitas;
#   };
#
# AVR-GCC TIDAK menambahkan padding pada struct, jadi format di bawah ini
# persis mengikuti urutan & ukuran field di atas, tanpa byte tambahan.
# ======================================================
PAYLOAD_FORMAT = "<8sfffhf"                       # '<' = little-endian, tanpa padding
PAYLOAD_SIZE = struct.calcsize(PAYLOAD_FORMAT)    # otomatis dihitung = 26 byte

# ======================================================
# DAFTAR BOX
# "key" harus SAMA PERSIS dengan BOX_ID di kode Arduino masing-masing box.
# Kalau Arduino Box 1 nanti pakai BOX_ID = "box001", pastikan cocok di sini.
# ======================================================
BOX_LABELS = {
    "box001": "Box 1",
    "box002": "Box 2",
    "box003": "Box 3",
    "box004": "Box 4",
}
BOX_ORDER = ["box001", "box002", "box003", "box004"]   # urutan tampil di GUI

# Box dianggap OFFLINE kalau sudah sekian detik tidak ada data baru masuk
OFFLINE_TIMEOUT_SEC = 10

# ======================================================
# LOGGING CSV
# ======================================================
DATA_DIR = "data"     # folder tempat file csv per-jam disimpan

# ======================================================
# SERVER (kirim data ke server tiap ada data sensor baru masuk)
# ======================================================
SERVER_ENABLED = True

# Ganti "box_monitor" di URL ini kalau nama folder di web server berbeda
# (lihat langkah upload PHP di README_SERVER.txt)
SERVER_URL = "http://103.163.184.28/box_monitor/receive_data.php"

# HARUS SAMA PERSIS dengan API_KEY di file receive_data.php di server.
# Ganti dengan kunci rahasia Anda sendiri (bebas, asal sama di 2 tempat).
SERVER_API_KEY = "boxmonitor-rahasia-ganti-ini"

SERVER_TIMEOUT_SEC = 5     # batas waktu tunggu respons server (detik)
SERVER_QUEUE_MAXSIZE = 200 # jaga-jaga kalau server mati lama, tidak memenuhi memori Pi
