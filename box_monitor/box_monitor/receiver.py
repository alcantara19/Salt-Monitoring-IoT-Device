"""
receiver.py
===========
Mengurus radio NRF24L01 dan menyimpan data terbaru tiap box ke memori.
Berjalan sebagai thread di background, dipanggil dari main.py.

TIDAK PERLU dijalankan terpisah dengan "python receiver.py".
Cukup jalankan "python main.py", nanti receiver ini otomatis ikut jalan.

CATATAN PENTING:
File ini sengaja memakai gaya API RF24 yang LAMA (camelCase):
    setPALevel(), setDataRate(), openReadingPipe(), startListening()
BUKAN gaya baru (open_rx_pipe(), listen=, set_radiation(), dst),
karena versi pyrf24 yang terpasang di Raspberry Pi ini terbukti hanya
bisa jalan dengan gaya lama (lihat script "receiver_yg_berhasil...py").
Jangan diganti ke gaya baru kecuali sudah dites ulang dan terbukti jalan.
"""

import struct
import threading
import time
import traceback

from pyrf24 import RF24, RF24_PA_LOW, RF24_PA_MIN, RF24_PA_HIGH, RF24_PA_MAX
from pyrf24 import RF24_1MBPS, RF24_2MBPS, RF24_250KBPS

import config
import logger
import server

_PA_LEVELS = {
    "MIN": RF24_PA_MIN,
    "LOW": RF24_PA_LOW,
    "HIGH": RF24_PA_HIGH,
    "MAX": RF24_PA_MAX,
}
_DATA_RATES = {
    "1MBPS": RF24_1MBPS,
    "2MBPS": RF24_2MBPS,
    "250KBPS": RF24_250KBPS,
}


class BoxReceiver:
    """
    Semua akses ke self.latest_data dilindungi lock, supaya aman dipakai
    bersamaan oleh thread radio dan thread GUI (Tkinter).
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.latest_data = {}     # box_id -> {"data": {...}, "last_seen": epoch_time}
        self.radio_ready = False  # False kalau radio gagal dibuka
        self.error_message = ""
        self._radio = None
        self._running = False
        self._thread = None
        self.server_sender = server.ServerSender()

    # ---------------- setup radio ----------------
    def _setup_radio(self):
        radio = RF24(config.CE_PIN, config.CSN_PIN)

        if not radio.begin():
            raise RuntimeError(
                "NRF24 tidak terdeteksi (radio.begin() gagal). Cek: wiring CE/CSN, "
                "SPI sudah aktif (sudo raspi-config -> Interface Options -> SPI), "
                "dan power 3.3V modul stabil."
            )

        # --- PENTING: pakai API lama (camelCase), sesuai versi pyrf24 di Pi ini ---
        radio.setPALevel(_PA_LEVELS[config.PA_LEVEL])
        radio.setDataRate(_DATA_RATES[config.DATA_RATE])

        # Sengaja TIDAK mengubah channel -> pakai default library (76),
        # sama seperti kode Arduino yang juga tidak mengubah channel.

        radio.openReadingPipe(1, config.RADIO_ADDRESS)
        radio.startListening()

        self._radio = radio
        self.radio_ready = True
        self.error_message = ""
        print("[receiver] NRF24 siap (API lama), menunggu data dari box...")
        print(f"[receiver] Expected payload size: {config.PAYLOAD_SIZE} bytes")

    # ---------------- decode payload ----------------
    @staticmethod
    def _decode(raw_bytes):
        box_id_raw, water_temp, air_temp, humidity, water_level, salinitas = (
            struct.unpack(config.PAYLOAD_FORMAT, raw_bytes)
        )
        box_id = box_id_raw.decode("ascii", errors="ignore").rstrip("\x00")

        values = {
            "salinitas": round(salinitas, 2),
            "air_temp": round(air_temp, 2),
            "water_temp": round(water_temp, 2),
            "humidity": round(humidity, 2),
            "water_level": water_level,
        }
        return box_id, values

    # ---------------- loop utama (background thread) ----------------
    def _run(self):
        try:
            self._setup_radio()
        except Exception as e:
            # Tangkap SEMUA jenis error (bukan cuma RuntimeError), supaya
            # kalau ada method/attribute yang tidak ada di versi pyrf24 ini,
            # errornya tetap kelihatan jelas di terminal, tidak diam-diam.
            self.error_message = str(e)
            self.radio_ready = False
            print("[receiver] GAGAL setup radio, detail error:")
            traceback.print_exc()
            return

        while self._running:
            try:
                if self._radio.available():
                    payload = self._radio.read(config.PAYLOAD_SIZE)

                    if len(payload) != config.PAYLOAD_SIZE:
                        print(f"[receiver] ERROR: payload size {len(payload)} "
                              f"(harusnya {config.PAYLOAD_SIZE}), dilewati.")
                        continue

                    try:
                        box_id, values = self._decode(payload)
                    except struct.error as e:
                        print(f"[receiver] Gagal decode payload: {e}")
                        continue

                    now = time.time()
                    with self.lock:
                        self.latest_data[box_id] = {"data": values, "last_seen": now}

                    logger.log_reading(box_id, values, now)
                    self.server_sender.send_async(box_id, values, now)
                    print(f"[receiver] {box_id}: {values}")
                else:
                    time.sleep(0.01)
            except Exception:
                # Jangan biarkan thread mati diam-diam kalau ada error tak
                # terduga saat loop baca data - print traceback lalu lanjut.
                print("[receiver] ERROR saat membaca data:")
                traceback.print_exc()
                time.sleep(0.5)

    # ---------------- API untuk GUI ----------------
    def start(self):
        self._running = True
        self.server_sender.start()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self.server_sender.stop()

    def get_box(self, box_id):
        """Ambil data terakhir 1 box. None kalau belum pernah menerima data box ini."""
        with self.lock:
            entry = self.latest_data.get(box_id)
            return dict(entry) if entry else None

    def is_online(self, box_id):
        entry = self.get_box(box_id)
        if entry is None:
            return False
        return (time.time() - entry["last_seen"]) <= config.OFFLINE_TIMEOUT_SEC
