"""
Styled dialog + dashboard window launcher for tray menu actions.

Two render modes:
  - Simple payload (default): single scrolling card list (existing behaviour).
  - Dashboard payload (payload['kind'] == 'dashboard'): tabbed window with
    Today / Settings / Audio / About panes. The Settings pane edits config
    in-place and writes ~/.athan_app/config.json, then drops a sentinel file
    so the running daemon picks the changes up.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


# Make config/utils importable when this script is launched as a subprocess.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


PALETTE = {
    "bg": "#0f2b1d",
    "panel": "#173826",
    "card": "#f5f1e8",
    "card_alt": "#e0f0d8",
    "text_dark": "#173826",
    "text_light": "#f8f5ef",
    "muted": "#7b8f83",
    "accent": "#c8a34d",
    "accent_soft": "#f3d995",
    "good": "#2e7d32",
    "warn": "#a8551a",
}


# Method id -> display label. Aladhan API methods.
CALCULATION_METHODS = [
    (0, "Jafari / Shia Ithna-Ashari"),
    (1, "University of Islamic Sciences, Karachi"),
    (2, "Islamic Society of North America (ISNA)"),
    (3, "Muslim World League"),
    (4, "Umm Al-Qura, Makkah"),
    (5, "Egyptian General Authority of Survey"),
    (7, "Institute of Geophysics, University of Tehran"),
    (8, "Gulf Region"),
    (9, "Kuwait"),
    (10, "Qatar"),
    (11, "Majlis Ugama Islam Singapura"),
    (12, "Union des Organisations Islamiques de France"),
    (13, "Diyanet İşleri Başkanlığı, Turkey"),
    (14, "Spiritual Administration of Muslims of Russia"),
    (15, "Moonsighting Committee Worldwide"),
    (16, "Dubai (unofficial)"),
    (17, "Jabatan Kemajuan Islam Malaysia (JAKIM)"),
    (18, "Tunisia"),
    (19, "Algeria"),
    (20, "KEMENAG - Kementerian Agama Republik Indonesia"),
    (21, "Morocco"),
    (22, "Comunidade Islamica de Lisboa"),
    (23, "Ministry of Awqaf, Jordan"),
]


# ---------------------------------------------------------------------------
# Decoding
# ---------------------------------------------------------------------------

def _decode_payload(encoded: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8"))


# ---------------------------------------------------------------------------
# Simple payload (existing behaviour, used by Next Prayer / Prayer Times / About)
# ---------------------------------------------------------------------------

def _make_scrollable_body(root: tk.Tk):
    canvas = tk.Canvas(root, bg=PALETTE["bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    body = tk.Frame(canvas, bg=PALETTE["bg"])

    body.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=body, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return body


def _card(parent: tk.Widget, title: str, subtitle: str = "", highlight: bool = False) -> tk.Frame:
    frame = tk.Frame(
        parent,
        bg=PALETTE["card_alt"] if highlight else PALETTE["card"],
        bd=0,
        highlightthickness=0,
        padx=16,
        pady=12,
    )
    frame.pack(fill="x", pady=8, padx=18)

    tk.Label(
        frame,
        text=title,
        bg=frame["bg"],
        fg=PALETTE["text_dark"],
        font=("Helvetica", 16, "bold"),
        anchor="w",
    ).pack(anchor="w")

    if subtitle:
        tk.Label(
            frame,
            text=subtitle,
            bg=frame["bg"],
            fg=PALETTE["muted"],
            font=("Helvetica", 11),
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

    return frame


def _section_title(parent: tk.Widget, text: str):
    tk.Label(
        parent,
        text=text,
        bg=PALETTE["bg"],
        fg=PALETTE["accent_soft"],
        font=("Helvetica", 13, "bold"),
        anchor="w",
    ).pack(anchor="w", padx=18, pady=(18, 6))


def _show_simple_payload(payload: dict):
    root = tk.Tk()
    root.title(payload.get("title", "Athan App"))
    root.geometry(payload.get("geometry", "620x720"))
    root.configure(bg=PALETTE["bg"])
    root.resizable(False, True)

    root.attributes("-topmost", True)
    root.after(400, lambda: root.attributes("-topmost", False))

    body = _make_scrollable_body(root)

    header = tk.Frame(body, bg=PALETTE["panel"], padx=20, pady=18)
    header.pack(fill="x", pady=(0, 14))

    tk.Label(
        header,
        text=payload.get("title", "Athan App"),
        bg=PALETTE["panel"],
        fg=PALETTE["text_light"],
        font=("Helvetica", 22, "bold"),
        anchor="w",
    ).pack(anchor="w")

    subtitle = payload.get("subtitle", "")
    if subtitle:
        tk.Label(
            header,
            text=subtitle,
            bg=PALETTE["panel"],
            fg="#cfe2d7",
            font=("Helvetica", 11),
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

    message = payload.get("message", "")
    if message:
        _card(body, payload.get("message_title", "Overview"), message, highlight=False)

    next_prayer = payload.get("next_prayer")
    if next_prayer:
        _section_title(body, "Next Prayer")
        _card(
            body,
            next_prayer.get("name", "Prayer"),
            next_prayer.get("formatted", ""),
            highlight=True,
        )

    prayer_times = payload.get("prayer_times", [])
    if prayer_times:
        _section_title(body, "Prayer Times")
        for prayer in prayer_times:
            _card(
                body,
                f"{prayer['label']}  {prayer['time']}",
                prayer.get("note", ""),
                highlight=prayer.get("highlight", False),
            )

    facts = payload.get("facts", [])
    if facts:
        _section_title(body, "Details")
        details = "\n".join(facts)
        _card(body, "Current Information", details, highlight=False)

    footer = tk.Frame(body, bg=PALETTE["bg"], pady=14)
    footer.pack(fill="x", padx=18)
    tk.Button(
        footer,
        text="Close",
        command=root.destroy,
        bg=PALETTE["accent"],
        fg=PALETTE["text_dark"],
        activebackground=PALETTE["accent_soft"],
        activeforeground=PALETTE["text_dark"],
        relief="flat",
        font=("Helvetica", 12, "bold"),
        padx=18,
        pady=8,
        cursor="hand2",
    ).pack(anchor="e")

    root.mainloop()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardWindow:
    """Tabbed dashboard with live Today view and an editable Settings form."""

    PRAYER_NAMES = ("fajr", "dhuhr", "asr", "maghrib", "isha")

    def __init__(self, payload: dict):
        self.payload = payload
        self.config = payload.get("config", {}) or {}
        self.prayer_times = payload.get("prayer_times_map", {}) or {}
        self.reminder_schedule = payload.get("reminder_schedule", {}) or {}
        self.custom_audio_schedule = payload.get("custom_audio_schedule", {}) or {}
        self.next_prayer = payload.get("next_prayer") or {}
        self.audio_info = payload.get("audio_info", {}) or {}

        self.root = tk.Tk()
        self.root.title(payload.get("title", "Athan App"))
        self.root.geometry(payload.get("geometry", "780x780"))
        self.root.configure(bg=PALETTE["bg"])
        self.root.minsize(720, 640)

        self.root.attributes("-topmost", True)
        self.root.after(500, lambda: self.root.attributes("-topmost", False))

        self._build_header()
        self._build_tabs()

        self.initial_tab = payload.get("initial_tab", "today")
        if self.initial_tab in self._tab_indices:
            self.notebook.select(self._tab_indices[self.initial_tab])

        self._tick()

    # ----- header --------------------------------------------------------

    def _build_header(self):
        header = tk.Frame(self.root, bg=PALETTE["panel"], padx=20, pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text=self.payload.get("title", "Athan App"),
            bg=PALETTE["panel"],
            fg=PALETTE["text_light"],
            font=("Helvetica", 20, "bold"),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            header,
            text=self.payload.get("subtitle", ""),
            bg=PALETTE["panel"],
            fg="#cfe2d7",
            font=("Helvetica", 10),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

    # ----- tabs ----------------------------------------------------------

    def _build_tabs(self):
        style = ttk.Style()
        try:
            style.theme_use("default")
        except tk.TclError:
            pass
        style.configure(
            "Athan.TNotebook",
            background=PALETTE["bg"],
            borderwidth=0,
        )
        style.configure(
            "Athan.TNotebook.Tab",
            background=PALETTE["panel"],
            foreground=PALETTE["text_light"],
            padding=(16, 8),
            font=("Helvetica", 11, "bold"),
        )
        style.map(
            "Athan.TNotebook.Tab",
            background=[("selected", PALETTE["accent"])],
            foreground=[("selected", PALETTE["text_dark"])],
        )

        self.notebook = ttk.Notebook(self.root, style="Athan.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self._tab_indices = {}

        today_tab = tk.Frame(self.notebook, bg=PALETTE["bg"])
        self.notebook.add(today_tab, text="Today")
        self._tab_indices["today"] = 0
        self._build_today_tab(today_tab)

        settings_tab = tk.Frame(self.notebook, bg=PALETTE["bg"])
        self.notebook.add(settings_tab, text="Settings")
        self._tab_indices["settings"] = 1
        self._build_settings_tab(settings_tab)

        audio_tab = tk.Frame(self.notebook, bg=PALETTE["bg"])
        self.notebook.add(audio_tab, text="Audio")
        self._tab_indices["audio"] = 2
        self._build_audio_tab(audio_tab)

        about_tab = tk.Frame(self.notebook, bg=PALETTE["bg"])
        self.notebook.add(about_tab, text="About")
        self._tab_indices["about"] = 3
        self._build_about_tab(about_tab)

    # ----- Today tab -----------------------------------------------------

    def _build_today_tab(self, parent: tk.Frame):
        wrapper = tk.Frame(parent, bg=PALETTE["bg"])
        wrapper.pack(fill="both", expand=True, padx=8, pady=8)

        # Countdown card
        self.countdown_card = tk.Frame(
            wrapper,
            bg=PALETTE["card_alt"],
            padx=20,
            pady=18,
        )
        self.countdown_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            self.countdown_card,
            text="Next Prayer",
            bg=PALETTE["card_alt"],
            fg=PALETTE["muted"],
            font=("Helvetica", 11, "bold"),
            anchor="w",
        ).pack(anchor="w")

        self.next_prayer_label = tk.Label(
            self.countdown_card,
            text="—",
            bg=PALETTE["card_alt"],
            fg=PALETTE["text_dark"],
            font=("Helvetica", 24, "bold"),
            anchor="w",
        )
        self.next_prayer_label.pack(anchor="w", pady=(2, 4))

        self.countdown_label = tk.Label(
            self.countdown_card,
            text="",
            bg=PALETTE["card_alt"],
            fg=PALETTE["good"],
            font=("Helvetica", 14),
            anchor="w",
        )
        self.countdown_label.pack(anchor="w")

        self.clock_label = tk.Label(
            self.countdown_card,
            text="",
            bg=PALETTE["card_alt"],
            fg=PALETTE["muted"],
            font=("Helvetica", 10),
            anchor="w",
        )
        self.clock_label.pack(anchor="w", pady=(6, 0))

        # Schedule list
        sched_frame = tk.LabelFrame(
            wrapper,
            text="  Today's schedule  ",
            bg=PALETTE["bg"],
            fg=PALETTE["accent_soft"],
            font=("Helvetica", 11, "bold"),
            bd=0,
        )
        sched_frame.pack(fill="both", expand=True)

        self.schedule_rows_frame = tk.Frame(sched_frame, bg=PALETTE["bg"])
        self.schedule_rows_frame.pack(fill="both", expand=True, padx=4, pady=6)

        self._render_schedule_rows()

    # Friendly labels for events shown in the schedule
    _EVENT_LABELS = {
        "fajr": "Fajr",
        "dhuhr": "Dhuhr",
        "asr": "Asr",
        "maghrib": "Maghrib",
        "isha": "Isha",
        "sunrise": "Sunrise",
        "morning_audio": "Morning Reminder",
        "night_audio": "Night Reminder",
        "friday_before_dhuhr": "Surat Al-Kahf (Fridays)",
    }

    def _render_schedule_rows(self):
        for child in self.schedule_rows_frame.winfo_children():
            child.destroy()

        # Track countdown labels so _tick can update them every second.
        # Each entry: (countdown_label, target_datetime, note_text)
        self._row_countdowns = []

        rows = []  # tuples of (label, time_str, note, highlight)

        next_name = self.next_prayer.get("prayer") if self.next_prayer else None

        for prayer in self.PRAYER_NAMES:
            time_str = self.prayer_times.get(prayer)
            if not time_str:
                continue
            note_parts = []
            reminder = self.reminder_schedule.get(f"pre_prayer_woduaa:{prayer}")
            if reminder:
                note_parts.append(f"Woduaa at {reminder}")
            if prayer == next_name:
                note_parts.insert(0, "Up next")
            rows.append((
                self._EVENT_LABELS.get(prayer, prayer.title()),
                time_str,
                "  ·  ".join(note_parts),
                prayer == next_name,
            ))

        sunrise = self.prayer_times.get("sunrise")
        if sunrise:
            rows.append((self._EVENT_LABELS["sunrise"], sunrise, "", False))

        for event_name, time_str in self.custom_audio_schedule.items():
            label = self._EVENT_LABELS.get(event_name, event_name.replace("_", " ").title())
            rows.append((label, time_str, "", False))

        if not rows:
            tk.Label(
                self.schedule_rows_frame,
                text="No prayer schedule loaded yet.",
                bg=PALETTE["bg"],
                fg=PALETTE["muted"],
                font=("Helvetica", 11),
            ).pack(pady=20)
            return

        now = datetime.now()
        for label, time_str, note, highlight in rows:
            row = tk.Frame(
                self.schedule_rows_frame,
                bg=PALETTE["card_alt"] if highlight else PALETTE["card"],
                padx=14,
                pady=10,
            )
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=label,
                bg=row["bg"],
                fg=PALETTE["text_dark"],
                font=("Helvetica", 13, "bold"),
                width=26,
                anchor="w",
            ).pack(side="left")

            tk.Label(
                row,
                text=time_str,
                bg=row["bg"],
                fg=PALETTE["text_dark"],
                font=("Helvetica", 13),
                width=8,
                anchor="w",
            ).pack(side="left")

            countdown_label = tk.Label(
                row,
                text="",
                bg=row["bg"],
                fg=PALETTE["good"],
                font=("Helvetica", 11, "bold"),
            )
            countdown_label.pack(side="right")

            if note:
                tk.Label(
                    row,
                    text=note,
                    bg=row["bg"],
                    fg=PALETTE["muted"],
                    font=("Helvetica", 10),
                ).pack(side="right", padx=(0, 12))

            target_dt = self._parse_today_time(time_str, now)
            self._row_countdowns.append((countdown_label, target_dt))

    def _tick(self):
        """Update the top countdown card and every per-row countdown."""
        now = datetime.now()
        self.clock_label.config(text=now.strftime("Now: %A %H:%M:%S"))

        next_info = self._compute_next_prayer(now)
        if next_info:
            name, prayer_dt = next_info
            delta = prayer_dt - now
            self.next_prayer_label.config(
                text=f"{self._EVENT_LABELS.get(name, name.title())} at {prayer_dt.strftime('%H:%M')}"
            )
            self.countdown_label.config(text=f"in {_format_countdown(delta)}")
        else:
            self.next_prayer_label.config(text="No upcoming prayer today")
            self.countdown_label.config(text="Refreshing at midnight")

        # Update each row's countdown.
        for label_widget, target_dt in getattr(self, "_row_countdowns", []):
            if target_dt is None:
                label_widget.config(text="", fg=PALETTE["muted"])
                continue
            delta = target_dt - now
            if delta.total_seconds() <= 0:
                label_widget.config(text="passed", fg=PALETTE["muted"])
            else:
                label_widget.config(text=f"in {_format_countdown(delta)}", fg=PALETTE["good"])

        self.root.after(1000, self._tick)

    @staticmethod
    def _parse_today_time(time_str: str, now: datetime):
        """Convert 'HH:MM' to a datetime on today's date. Returns None on failure."""
        try:
            hour, minute = (int(part) for part in time_str.split(":")[:2])
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except (ValueError, AttributeError):
            return None

    def _compute_next_prayer(self, now: datetime):
        upcoming = []
        for prayer in self.PRAYER_NAMES:
            time_str = self.prayer_times.get(prayer)
            if not time_str:
                continue
            try:
                hour, minute = (int(part) for part in time_str.split(":"))
            except ValueError:
                continue
            prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if prayer_dt > now:
                upcoming.append((prayer, prayer_dt))
        if not upcoming:
            return None
        return min(upcoming, key=lambda item: item[1])

    # ----- Settings tab --------------------------------------------------

    def _build_settings_tab(self, parent: tk.Frame):
        canvas = tk.Canvas(parent, bg=PALETTE["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=PALETTE["bg"])

        body.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=body, anchor="nw", width=720)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.settings_vars = {}

        self._build_location_section(body)
        self._build_prayer_section(body)
        self._build_audio_volume_section(body)
        self._build_special_audio_section(body)
        self._build_settings_actions(body)

    def _build_location_section(self, parent: tk.Frame):
        section = self._section_box(parent, "Location")

        loc = self.config.get("location", {})

        self.settings_vars["location.auto_detect"] = tk.BooleanVar(
            value=bool(loc.get("auto_detect", True))
        )
        tk.Checkbutton(
            section,
            text="Auto-detect location at startup",
            variable=self.settings_vars["location.auto_detect"],
            bg=PALETTE["card"],
            fg=PALETTE["text_dark"],
            activebackground=PALETTE["card"],
            selectcolor=PALETTE["card_alt"],
            anchor="w",
            font=("Helvetica", 11),
        ).pack(anchor="w", pady=(0, 8))

        for key, label in [
            ("city", "City"),
            ("state", "State / Region"),
            ("country", "Country"),
            ("timezone", "Timezone"),
            ("latitude", "Latitude"),
            ("longitude", "Longitude"),
        ]:
            self._labeled_entry(section, f"location.{key}", label, str(loc.get(key, "")))

    def _build_prayer_section(self, parent: tk.Frame):
        section = self._section_box(parent, "Prayer calculation")

        prayer_settings = self.config.get("prayer_settings", {})
        method = int(prayer_settings.get("calculation_method", 2))

        method_label_to_id = {f"{mid}: {label}": mid for mid, label in CALCULATION_METHODS}
        method_id_to_label = {mid: label for label, mid in method_label_to_id.items()}
        current_label = method_id_to_label.get(method, f"{method}: Custom")

        method_var = tk.StringVar(value=current_label)
        self.settings_vars["prayer_settings.calculation_method"] = (method_var, method_label_to_id)

        row = tk.Frame(section, bg=PALETTE["card"])
        row.pack(fill="x", pady=4)
        tk.Label(
            row,
            text="Calculation method",
            bg=PALETTE["card"],
            fg=PALETTE["text_dark"],
            font=("Helvetica", 11),
            width=22,
            anchor="w",
        ).pack(side="left")
        ttk.Combobox(
            row,
            textvariable=method_var,
            values=list(method_label_to_id.keys()),
            state="readonly",
            width=46,
        ).pack(side="left", fill="x", expand=True)

        tk.Label(
            section,
            text="Enabled prayers",
            bg=PALETTE["card"],
            fg=PALETTE["text_dark"],
            font=("Helvetica", 11, "bold"),
        ).pack(anchor="w", pady=(12, 4))

        enabled = prayer_settings.get("enabled_prayers", {})
        prayers_row = tk.Frame(section, bg=PALETTE["card"])
        prayers_row.pack(anchor="w")
        for prayer in self.PRAYER_NAMES:
            var = tk.BooleanVar(value=bool(enabled.get(prayer, True)))
            self.settings_vars[f"prayer_settings.enabled_prayers.{prayer}"] = var
            tk.Checkbutton(
                prayers_row,
                text=prayer.title(),
                variable=var,
                bg=PALETTE["card"],
                fg=PALETTE["text_dark"],
                activebackground=PALETTE["card"],
                selectcolor=PALETTE["card_alt"],
                font=("Helvetica", 11),
            ).pack(side="left", padx=4)

    def _build_audio_volume_section(self, parent: tk.Frame):
        section = self._section_box(parent, "Audio volumes")

        audio = self.config.get("audio_settings", {})
        self._labeled_entry(
            section,
            "audio_settings.volume",
            "Master volume (0.0–1.0)",
            str(audio.get("volume", 0.8)),
        )
        self._labeled_entry(
            section,
            "audio_settings.athan_volume",
            "Athan volume (0.0–1.0)",
            str(audio.get("athan_volume", 0.8)),
        )

    def _build_special_audio_section(self, parent: tk.Frame):
        section = self._section_box(parent, "Reminders & special audio")

        special = self.config.get("special_audio_settings", {})

        self._special_event_row(
            section,
            "pre_prayer_woduaa",
            "Pre-prayer Woduaa reminder",
            special.get("pre_prayer_woduaa", {}),
            offset_field=("lead_minutes", "Minutes before prayer"),
        )
        self._special_event_row(
            section,
            "after_prayer_duaa",
            "After-prayer Duaa",
            special.get("after_prayer_duaa", {}),
            offset_field=None,
        )
        self._special_event_row(
            section,
            "friday_before_dhuhr",
            "Friday — Surat Al-Kahf",
            special.get("friday_before_dhuhr", {}),
            offset_field=("offset_minutes", "Offset min (negative = before)"),
        )
        self._special_event_row(
            section,
            "morning_audio",
            "Morning audio (relative to Dhuhr)",
            special.get("morning_audio", {}),
            offset_field=("offset_minutes", "Offset min (negative = before)"),
        )
        self._special_event_row(
            section,
            "night_audio",
            "Night audio (relative to Asr)",
            special.get("night_audio", {}),
            offset_field=("offset_minutes", "Offset min (positive = after)"),
        )

    def _special_event_row(
        self,
        parent: tk.Frame,
        event_name: str,
        label: str,
        cfg: dict,
        offset_field,
    ):
        box = tk.Frame(parent, bg=PALETTE["card_alt"], padx=12, pady=10)
        box.pack(fill="x", pady=6)

        head = tk.Frame(box, bg=PALETTE["card_alt"])
        head.pack(fill="x")

        enabled_var = tk.BooleanVar(value=bool(cfg.get("enabled", False)))
        self.settings_vars[f"special_audio_settings.{event_name}.enabled"] = enabled_var
        tk.Checkbutton(
            head,
            text=label,
            variable=enabled_var,
            bg=PALETTE["card_alt"],
            fg=PALETTE["text_dark"],
            activebackground=PALETTE["card_alt"],
            selectcolor=PALETTE["card"],
            font=("Helvetica", 12, "bold"),
        ).pack(side="left")

        if offset_field:
            field_key, field_label = offset_field
            row = tk.Frame(box, bg=PALETTE["card_alt"])
            row.pack(fill="x", pady=(8, 4))
            tk.Label(
                row,
                text=field_label,
                bg=PALETTE["card_alt"],
                fg=PALETTE["text_dark"],
                font=("Helvetica", 10),
                width=30,
                anchor="w",
            ).pack(side="left")
            value_var = tk.StringVar(value=str(cfg.get(field_key, 0)))
            self.settings_vars[f"special_audio_settings.{event_name}.{field_key}"] = value_var
            tk.Entry(row, textvariable=value_var, width=10).pack(side="left")

        # Volume + audio file
        vol_row = tk.Frame(box, bg=PALETTE["card_alt"])
        vol_row.pack(fill="x", pady=(4, 4))
        tk.Label(
            vol_row,
            text="Volume (0.0–1.0)",
            bg=PALETTE["card_alt"],
            fg=PALETTE["text_dark"],
            font=("Helvetica", 10),
            width=30,
            anchor="w",
        ).pack(side="left")
        vol_var = tk.StringVar(value=str(cfg.get("volume", 0.8)))
        self.settings_vars[f"special_audio_settings.{event_name}.volume"] = vol_var
        tk.Entry(vol_row, textvariable=vol_var, width=10).pack(side="left")

        file_row = tk.Frame(box, bg=PALETTE["card_alt"])
        file_row.pack(fill="x", pady=(4, 0))
        tk.Label(
            file_row,
            text="Audio file",
            bg=PALETTE["card_alt"],
            fg=PALETTE["text_dark"],
            font=("Helvetica", 10),
            width=30,
            anchor="w",
        ).pack(side="left")
        file_var = tk.StringVar(value=str(cfg.get("audio_file", "")))
        self.settings_vars[f"special_audio_settings.{event_name}.audio_file"] = file_var
        tk.Entry(file_row, textvariable=file_var).pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(
            file_row,
            text="Browse…",
            command=lambda v=file_var: self._browse_audio(v),
            bg=PALETTE["accent"],
            fg=PALETTE["text_dark"],
            activebackground=PALETTE["accent_soft"],
            relief="flat",
            cursor="hand2",
        ).pack(side="left")
        tk.Button(
            file_row,
            text="▶ Test",
            command=lambda v=file_var: self._test_play(v.get()),
            bg=PALETTE["good"],
            fg=PALETTE["text_dark"],
            activebackground=PALETTE["accent_soft"],
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(6, 0))
        tk.Button(
            file_row,
            text="■ Stop",
            command=self._stop_test_play,
            bg=PALETTE["card"],
            fg=PALETTE["text_dark"],
            activebackground=PALETTE["accent_soft"],
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(4, 0))

    def _browse_audio(self, var: tk.StringVar):
        path = filedialog.askopenfilename(
            title="Choose audio file",
            filetypes=[
                ("Audio files", "*.m4a *.mp3 *.wav *.ogg *.aac"),
                ("All files", "*.*"),
            ],
        )
        if path:
            var.set(path)

    # ---- audio test ------------------------------------------------------
    _test_proc = None  # process handle for the currently-playing test

    def _resolve_test_audio_path(self, path_str: str) -> str:
        """Resolve a possibly-relative config path to an absolute existing file."""
        import os
        from pathlib import Path
        from utils.app_paths import get_audio_search_dirs, get_config_dir, get_bundle_root

        if not path_str:
            return ""
        if os.path.isabs(path_str) and os.path.exists(path_str):
            return path_str
        # Mirror the runtime resolver: check config dir, bundle, then audio search dirs.
        candidates = [get_config_dir() / path_str, get_bundle_root() / path_str]
        for c in candidates:
            if c.exists():
                return str(c)
        filename = os.path.basename(path_str)
        for d in get_audio_search_dirs():
            cand = d / filename
            if cand.exists():
                return str(cand)
        return ""

    def _test_play(self, path_str: str):
        """Play the given audio file via afplay. Stops any previous test."""
        import subprocess, tkinter.messagebox as _mb
        resolved = self._resolve_test_audio_path(path_str)
        if not resolved:
            _mb.showerror("Test audio", f"Could not find audio file:\n{path_str}")
            return
        self._stop_test_play()
        try:
            DashboardWindow._test_proc = subprocess.Popen(
                ["/usr/bin/afplay", resolved],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Safety cap: stop the test after 60s automatically.
            self.root.after(60_000, self._stop_test_play)
        except Exception as e:
            _mb.showerror("Test audio", f"Failed to play:\n{e}")

    def _stop_test_play(self):
        """Kill the currently-running test, if any."""
        proc = DashboardWindow._test_proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        DashboardWindow._test_proc = None

    def _labeled_entry(self, parent: tk.Frame, key: str, label: str, value: str):
        row = tk.Frame(parent, bg=PALETTE["card"])
        row.pack(fill="x", pady=4)
        tk.Label(
            row,
            text=label,
            bg=PALETTE["card"],
            fg=PALETTE["text_dark"],
            font=("Helvetica", 11),
            width=22,
            anchor="w",
        ).pack(side="left")
        var = tk.StringVar(value=value)
        self.settings_vars[key] = var
        tk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

    def _section_box(self, parent: tk.Frame, title: str) -> tk.Frame:
        tk.Label(
            parent,
            text=title,
            bg=PALETTE["bg"],
            fg=PALETTE["accent_soft"],
            font=("Helvetica", 13, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(14, 4))

        box = tk.Frame(parent, bg=PALETTE["card"], padx=16, pady=14)
        box.pack(fill="x", padx=14)
        return box

    def _build_settings_actions(self, parent: tk.Frame):
        bar = tk.Frame(parent, bg=PALETTE["bg"], pady=20)
        bar.pack(fill="x", padx=14)

        self.settings_status_label = tk.Label(
            bar,
            text="",
            bg=PALETTE["bg"],
            fg=PALETTE["good"],
            font=("Helvetica", 10),
        )
        self.settings_status_label.pack(side="left")

        tk.Button(
            bar,
            text="Save changes",
            command=self._save_settings,
            bg=PALETTE["accent"],
            fg=PALETTE["text_dark"],
            activebackground=PALETTE["accent_soft"],
            activeforeground=PALETTE["text_dark"],
            relief="flat",
            font=("Helvetica", 11, "bold"),
            padx=18,
            pady=8,
            cursor="hand2",
        ).pack(side="right")

    def _save_settings(self):
        try:
            from config.settings import ConfigManager
            from utils.app_paths import get_config_dir
        except Exception as exc:
            messagebox.showerror("Save failed", f"Could not import config module:\n{exc}")
            return

        try:
            cm = ConfigManager()
            errors = self._collect_settings_into(cm)
            if errors:
                messagebox.showerror("Invalid values", "\n".join(errors))
                return
            if not cm.save_config():
                messagebox.showerror("Save failed", "Could not write config.json")
                return

            # Drop a sentinel so the running daemon knows to reload.
            sentinel = get_config_dir() / ".reload_request"
            try:
                sentinel.write_text(str(int(datetime.now().timestamp())))
            except OSError:
                pass

            self.settings_status_label.config(
                text="Saved. Changes apply within a few seconds.",
                fg=PALETTE["good"],
            )
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    def _collect_settings_into(self, cm) -> list:
        errors = []

        def _set_float(key, value, lo=None, hi=None):
            try:
                f = float(value)
            except (TypeError, ValueError):
                errors.append(f"{key}: not a number")
                return
            if lo is not None and f < lo:
                errors.append(f"{key}: must be ≥ {lo}")
                return
            if hi is not None and f > hi:
                errors.append(f"{key}: must be ≤ {hi}")
                return
            cm.set(key, f)

        def _set_int(key, value):
            try:
                cm.set(key, int(float(value)))
            except (TypeError, ValueError):
                errors.append(f"{key}: not an integer")

        # Location
        cm.set("location.auto_detect", bool(self.settings_vars["location.auto_detect"].get()))
        for str_key in ("city", "state", "country", "timezone"):
            cm.set(f"location.{str_key}", self.settings_vars[f"location.{str_key}"].get().strip())
        _set_float("location.latitude", self.settings_vars["location.latitude"].get(), -90, 90)
        _set_float("location.longitude", self.settings_vars["location.longitude"].get(), -180, 180)

        # Prayer settings
        method_var, method_label_to_id = self.settings_vars["prayer_settings.calculation_method"]
        cm.set("prayer_settings.calculation_method", int(method_label_to_id.get(method_var.get(), 2)))
        for prayer in self.PRAYER_NAMES:
            cm.set(
                f"prayer_settings.enabled_prayers.{prayer}",
                bool(self.settings_vars[f"prayer_settings.enabled_prayers.{prayer}"].get()),
            )

        # Audio volumes
        _set_float("audio_settings.volume", self.settings_vars["audio_settings.volume"].get(), 0.0, 1.0)
        _set_float(
            "audio_settings.athan_volume",
            self.settings_vars["audio_settings.athan_volume"].get(),
            0.0,
            1.0,
        )

        # Special audio events
        for event in (
            "pre_prayer_woduaa",
            "after_prayer_duaa",
            "friday_before_dhuhr",
            "morning_audio",
            "night_audio",
        ):
            base = f"special_audio_settings.{event}"
            cm.set(f"{base}.enabled", bool(self.settings_vars[f"{base}.enabled"].get()))
            _set_float(f"{base}.volume", self.settings_vars[f"{base}.volume"].get(), 0.0, 1.0)
            audio_path = self.settings_vars[f"{base}.audio_file"].get().strip()
            if audio_path:
                cm.set(f"{base}.audio_file", audio_path)
            if event == "pre_prayer_woduaa":
                _set_int(f"{base}.lead_minutes", self.settings_vars[f"{base}.lead_minutes"].get())
            elif event in ("friday_before_dhuhr", "morning_audio", "night_audio"):
                _set_int(f"{base}.offset_minutes", self.settings_vars[f"{base}.offset_minutes"].get())

        return errors

    # ----- Audio tab -----------------------------------------------------

    def _build_audio_tab(self, parent: tk.Frame):
        wrapper = tk.Frame(parent, bg=PALETTE["bg"])
        wrapper.pack(fill="both", expand=True, padx=16, pady=16)

        info = self.audio_info or {}

        rows = []
        default_audio = info.get("default_audio_file")
        if default_audio:
            rows.append(("Default Athan", default_audio, info.get("audio_file_exists", False)))

        for prayer, path in (info.get("prayer_audio_files") or {}).items():
            rows.append((f"{prayer.title()} Athan", path, os.path.exists(path)))

        for key, path in (info.get("special_audio_files") or {}).items():
            rows.append((key.replace("_", " ").title(), path, os.path.exists(path)))

        if not rows:
            tk.Label(
                wrapper,
                text="No audio files are currently loaded.",
                bg=PALETTE["bg"],
                fg=PALETTE["muted"],
                font=("Helvetica", 11),
            ).pack(pady=20)
            return

        for label, path, exists in rows:
            row = tk.Frame(wrapper, bg=PALETTE["card"], padx=14, pady=10)
            row.pack(fill="x", pady=4)
            tk.Label(
                row,
                text=label,
                bg=PALETTE["card"],
                fg=PALETTE["text_dark"],
                font=("Helvetica", 12, "bold"),
                width=24,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                row,
                text=os.path.basename(path) if path else "—",
                bg=PALETTE["card"],
                fg=PALETTE["text_dark"],
                font=("Helvetica", 11),
                anchor="w",
            ).pack(side="left", padx=(8, 8))
            tk.Label(
                row,
                text="✔ ready" if exists else "missing",
                bg=PALETTE["card"],
                fg=PALETTE["good"] if exists else PALETTE["warn"],
                font=("Helvetica", 10, "bold"),
            ).pack(side="right")

    # ----- About tab -----------------------------------------------------

    def _build_about_tab(self, parent: tk.Frame):
        wrapper = tk.Frame(parent, bg=PALETTE["bg"])
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(
            wrapper,
            text="Athan App",
            bg=PALETTE["bg"],
            fg=PALETTE["text_light"],
            font=("Helvetica", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            wrapper,
            text="Islamic prayer time companion",
            bg=PALETTE["bg"],
            fg=PALETTE["accent_soft"],
            font=("Helvetica", 12),
        ).pack(anchor="w", pady=(2, 16))

        for line in self.payload.get(
            "about_lines",
            [
                "Calculates prayer times from your location and plays your configured Athan and reminder audio automatically.",
                "Built with Python, VLC, and a macOS menu-bar launcher.",
                "Configuration: ~/.athan_app/config.json",
                "Audio overrides: ~/.athan_app/assets/audio/",
                "Logs: ~/.athan_app/athan_app.log",
            ],
        ):
            tk.Label(
                wrapper,
                text=f"•  {line}",
                bg=PALETTE["bg"],
                fg=PALETTE["text_light"],
                font=("Helvetica", 11),
                wraplength=620,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=2)

    # ----- run -----------------------------------------------------------

    def run(self):
        self.root.mainloop()


def _format_countdown(delta: timedelta) -> str:
    total_seconds = max(0, int(delta.total_seconds()))
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"in {hours}h {minutes:02d}m {seconds:02d}s"
    if minutes:
        return f"in {minutes}m {seconds:02d}s"
    return f"in {seconds}s"


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def show_payload(payload: dict):
    if payload.get("kind") == "dashboard":
        DashboardWindow(payload).run()
    else:
        _show_simple_payload(payload)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: main_window.py <payload>")

    payload = _decode_payload(sys.argv[1])
    show_payload(payload)


if __name__ == "__main__":
    main()
