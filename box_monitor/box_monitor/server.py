"""
server.py
=========
Mengirim tiap data sensor yang diterima ke server (PHP) lewat HTTP POST.

Didesain supaya TIDAK memblokir pembacaan radio NRF24:
- Data yang mau dikirim dimasukkan ke antrean (queue.Queue).
- Ada 1 thread terpisah yang ambil data dari antrean lalu kirim ke server.
- Kalau server lambat/mati, radio tetap terus membaca data seperti biasa;
  paling data ke server yang tertunda/hilang (di-drop) kalau antrean penuh,
  tapi data LOKAL (GUI + CSV) tidak terganggu sama sekali.

Tidak perlu dijalankan terpisah, otomatis dipakai oleh receiver.py.
"""

import json
import queue
import threading
import time

import requests

import config


class ServerSender:
    def __init__(self):
        self._queue = queue.Queue(maxsize=config.SERVER_QUEUE_MAXSIZE)
        self._running = False
        self._thread = None

        # status buat ditampilkan di GUI kalau perlu nanti
        self.last_success_time = None
        self.last_error = ""

    def start(self):
        if not config.SERVER_ENABLED:
            print("[server] SERVER_ENABLED = False, pengiriman ke server dimatikan.")
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        print(f"[server] Siap mengirim data ke {config.SERVER_URL}")

    def stop(self):
        self._running = False

    def send_async(self, box_id, values, epoch_time):
        """
        Dipanggil oleh receiver.py setiap ada data baru masuk.
        Tidak menunggu hasil kirim (non-blocking) - langsung return.
        """
        if not config.SERVER_ENABLED:
            return

        payload = {
            "box_id": box_id,
            "salinitas": values["salinitas"],
            "air_temp": values["air_temp"],
            "water_temp": values["water_temp"],
            "humidity": values["humidity"],
            "water_level": values["water_level"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time)),
            "api_key": config.SERVER_API_KEY,
        }

        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            # Server kemungkinan mati/lambat lama -> antrean penuh.
            # Buang data TERLAMA supaya antrean tidak macet permanen.
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(payload)
            except queue.Empty:
                pass
            print("[server] WARNING: antrean penuh, data lama di-drop "
                  "(server kemungkinan lambat/tidak merespons).")

    # ---------------- worker thread ----------------
    def _worker(self):
        session = requests.Session()

        while self._running:
            try:
                payload = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                response = session.post(
                    config.SERVER_URL,
                    json=payload,
                    timeout=config.SERVER_TIMEOUT_SEC,
                )

                if response.status_code == 200:
                    self.last_success_time = time.time()
                    self.last_error = ""
                    print(f"[server] OK  -> {payload['box_id']} tersimpan di server.")
                else:
                    self.last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    print(f"[server] GAGAL (HTTP {response.status_code}) untuk "
                          f"{payload['box_id']}: {response.text[:200]}")

            except requests.exceptions.RequestException as e:
                self.last_error = str(e)
                print(f"[server] GAGAL kirim {payload['box_id']} ke server: {e}")
                # tidak retry otomatis di sini supaya antrean tidak menumpuk;
                # data berikutnya akan tetap dicoba kirim seperti biasa.
