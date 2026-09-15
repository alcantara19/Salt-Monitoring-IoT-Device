"""
main.py
=======
Program utama. Menjalankan SEMUANYA sekaligus:
    - Radio NRF24 (receiver.py) -> jalan di background thread
    - GUI dashboard (Tkinter)   -> 2 halaman: daftar box & detail box
    - Logger CSV (logger.py)    -> otomatis tiap ada data masuk

Cara menjalankan di Raspberry Pi:

    cd /home/pi/box_monitor
    source /home/pi/nrf24-env/bin/activate
    python main.py

Cukup 1 perintah ini saja, tidak perlu jalankan receiver.py terpisah.
"""

import time
import tkinter as tk
from tkinter import font as tkfont

import config
from receiver import BoxReceiver

REFRESH_MS = 500   # seberapa sering GUI membaca data terbaru dari receiver
CLOCK_MS = 1000    # seberapa sering jam diperbarui

BG_COLOR = "#0f1720"
CARD_BG = "#1c2733"
CARD_BG_OFFLINE = "#2a1d1d"
ONLINE_COLOR = "#3ddc84"
OFFLINE_COLOR = "#ff5c5c"
TEXT_COLOR = "#e6edf3"
MUTED_COLOR = "#8b98a5"


class BoxMonitorApp(tk.Tk):
    def __init__(self, box_receiver: BoxReceiver):
        super().__init__()
        self.box_receiver = box_receiver

        self.title("Box Monitor")
        self.geometry("800x480")
        self.configure(bg=BG_COLOR)

        # ---------------- Fullscreen ----------------
        # F11       -> toggle fullscreen ON/OFF
        # Esc       -> keluar dari fullscreen (balik ke jendela biasa)
        self.is_fullscreen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        # font
        self.font_title = tkfont.Font(family="Helvetica", size=22, weight="bold")
        self.font_card_title = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.font_card_value = tkfont.Font(family="Helvetica", size=20, weight="bold")
        self.font_normal = tkfont.Font(family="Helvetica", size=12)
        self.font_detail_label = tkfont.Font(family="Helvetica", size=13)
        self.font_detail_value = tkfont.Font(family="Helvetica", size=18, weight="bold")

        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for PageClass in (DashboardPage, DetailPage):
            frame = PageClass(parent=container, app=self)
            self.frames[PageClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("DashboardPage")

        # loop update
        self.after(CLOCK_MS, self._tick_clock)
        self.after(REFRESH_MS, self._tick_data)

    # ---------------- Fullscreen ----------------
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)

    def show_frame(self, name, box_id=None):
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            frame.on_show(box_id)
        frame.tkraise()

    def _tick_clock(self):
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        self.frames["DashboardPage"].set_clock(now_str)
        self.frames["DetailPage"].set_clock(now_str)
        self.after(CLOCK_MS, self._tick_clock)

    def _tick_data(self):
        self.frames["DashboardPage"].refresh_data()
        self.frames["DetailPage"].refresh_data()
        self.after(REFRESH_MS, self._tick_data)


class DashboardPage(tk.Frame):
    """Halaman 1: menampilkan 4 kotak box, masing-masing bisa diklik."""

    def __init__(self, parent, app: BoxMonitorApp):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.cards = {}   # box_id -> dict of widgets

        top_bar = tk.Frame(self, bg=BG_COLOR)
        top_bar.pack(fill="x", padx=20, pady=(15, 0))

        fs_btn = tk.Button(top_bar, text="⛶ Fullscreen", font=app.font_normal,
                            command=app.toggle_fullscreen,
                            bg="#2f3b47", fg=TEXT_COLOR, relief="flat",
                            activebackground="#3c4a58", activeforeground=TEXT_COLOR,
                            padx=10, pady=4, cursor="hand2")
        fs_btn.pack(side="right")

        title = tk.Label(self, text="BOX MONITOR", font=app.font_title,
                          bg=BG_COLOR, fg=TEXT_COLOR)
        title.pack(pady=(10, 10))

        grid_frame = tk.Frame(self, bg=BG_COLOR)
        grid_frame.pack(expand=True, fill="both", padx=30)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for box_id, (r, c) in zip(config.BOX_ORDER, positions):
            card = self._build_card(grid_frame, box_id)
            card.grid(row=r, column=c, padx=15, pady=15, sticky="nsew")

        self.clock_label = tk.Label(self, text="", font=app.font_normal,
                                     bg=BG_COLOR, fg=MUTED_COLOR)
        self.clock_label.pack(pady=(5, 15))

    def _build_card(self, parent, box_id):
        label = config.BOX_LABELS.get(box_id, box_id)

        card = tk.Frame(parent, bg=CARD_BG, cursor="hand2",
                         highlightthickness=1, highlightbackground="#2f3b47")

        name_lbl = tk.Label(card, text=label, font=self.app.font_card_title,
                             bg=CARD_BG, fg=TEXT_COLOR)
        name_lbl.pack(pady=(20, 5))

        value_lbl = tk.Label(card, text="-- ppt", font=self.app.font_card_value,
                              bg=CARD_BG, fg=TEXT_COLOR)
        value_lbl.pack()

        caption_lbl = tk.Label(card, text="Salinitas", font=self.app.font_normal,
                                bg=CARD_BG, fg=MUTED_COLOR)
        caption_lbl.pack(pady=(0, 10))

        status_lbl = tk.Label(card, text="OFFLINE", font=self.app.font_normal,
                               bg=CARD_BG, fg=OFFLINE_COLOR)
        status_lbl.pack(pady=(0, 20))

        # semua widget di dalam card ikut bisa diklik
        widgets = [card, name_lbl, value_lbl, caption_lbl, status_lbl]
        for w in widgets:
            w.bind("<Button-1>", lambda e, bid=box_id: self.app.show_frame("DetailPage", bid))

        self.cards[box_id] = {
            "card": card,
            "value": value_lbl,
            "status": status_lbl,
        }
        return card

    def set_clock(self, text):
        self.clock_label.config(text=text)

    def refresh_data(self):
        for box_id, widgets in self.cards.items():
            entry = self.app.box_receiver.get_box(box_id)
            online = self.app.box_receiver.is_online(box_id)

            if entry is not None:
                salinitas = entry["data"]["salinitas"]
                widgets["value"].config(text=f"{salinitas:.2f} ppt")
            else:
                widgets["value"].config(text="-- ppt")

            if online:
                widgets["status"].config(text="ONLINE", fg=ONLINE_COLOR)
                widgets["card"].config(bg=CARD_BG)
            else:
                widgets["status"].config(text="OFFLINE", fg=OFFLINE_COLOR)
                widgets["card"].config(bg=CARD_BG_OFFLINE)


class DetailPage(tk.Frame):
    """Halaman 2: detail lengkap 1 box. Muncul setelah kotak di dashboard diklik."""

    def __init__(self, parent, app: BoxMonitorApp):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.current_box_id = None

        top_bar = tk.Frame(self, bg=BG_COLOR)
        top_bar.pack(fill="x", padx=20, pady=(20, 0))

        back_btn = tk.Button(top_bar, text="< BACK", font=app.font_normal,
                              command=lambda: app.show_frame("DashboardPage"),
                              bg="#2f3b47", fg=TEXT_COLOR, relief="flat",
                              activebackground="#3c4a58", activeforeground=TEXT_COLOR,
                              padx=15, pady=5, cursor="hand2")
        back_btn.pack(side="left")

        self.status_badge = tk.Label(top_bar, text="OFFLINE", font=app.font_normal,
                                      bg=BG_COLOR, fg=OFFLINE_COLOR)
        self.status_badge.pack(side="right")

        self.title_label = tk.Label(self, text="Box", font=app.font_title,
                                     bg=BG_COLOR, fg=TEXT_COLOR)
        self.title_label.pack(pady=(10, 20))

        detail_frame = tk.Frame(self, bg=BG_COLOR)
        detail_frame.pack(expand=True, fill="both", padx=40)
        detail_frame.grid_columnconfigure(0, weight=1)
        detail_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("salinitas", "Salinitas", "ppt"),
            ("water_temp", "Water Temperature", "°C"),
            ("air_temp", "Air Temperature", "°C"),
            ("humidity", "Humidity", "%"),
            ("water_level", "Water Level (ADC)", ""),
        ]

        self.value_labels = {}
        for i, (key, label, unit) in enumerate(fields):
            r, c = divmod(i, 2)
            box = tk.Frame(detail_frame, bg=CARD_BG, highlightthickness=1,
                            highlightbackground="#2f3b47")
            box.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")

            tk.Label(box, text=label, font=app.font_detail_label,
                     bg=CARD_BG, fg=MUTED_COLOR).pack(pady=(15, 5))

            value_lbl = tk.Label(box, text=f"-- {unit}".strip(), font=app.font_detail_value,
                                  bg=CARD_BG, fg=TEXT_COLOR)
            value_lbl.pack(pady=(0, 15))

            self.value_labels[key] = (value_lbl, unit)

        self.last_update_label = tk.Label(self, text="", font=app.font_normal,
                                           bg=BG_COLOR, fg=MUTED_COLOR)
        self.last_update_label.pack(pady=(5, 5))

        self.clock_label = tk.Label(self, text="", font=app.font_normal,
                                     bg=BG_COLOR, fg=MUTED_COLOR)
        self.clock_label.pack(pady=(0, 15))

    def on_show(self, box_id):
        self.current_box_id = box_id
        label = config.BOX_LABELS.get(box_id, box_id)
        self.title_label.config(text=label)
        self.refresh_data()

    def set_clock(self, text):
        self.clock_label.config(text=text)

    def refresh_data(self):
        if self.current_box_id is None:
            return

        box_id = self.current_box_id
        entry = self.app.box_receiver.get_box(box_id)
        online = self.app.box_receiver.is_online(box_id)

        if online:
            self.status_badge.config(text="ONLINE", fg=ONLINE_COLOR)
        else:
            self.status_badge.config(text="OFFLINE", fg=OFFLINE_COLOR)

        if entry is not None:
            data = entry["data"]
            for key, (lbl, unit) in self.value_labels.items():
                val = data.get(key, "--")
                text = f"{val} {unit}".strip() if not isinstance(val, float) else f"{val:.2f} {unit}".strip()
                lbl.config(text=text)

            last_seen_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["last_seen"]))
            self.last_update_label.config(text=f"Update terakhir: {last_seen_str}")
        else:
            for lbl, unit in self.value_labels.values():
                lbl.config(text=f"-- {unit}".strip())
            self.last_update_label.config(text="Belum ada data masuk untuk box ini")


def main():
    box_receiver = BoxReceiver()
    box_receiver.start()

    app = BoxMonitorApp(box_receiver)

    def on_close():
        box_receiver.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
