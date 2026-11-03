import sys
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import requests
import random
import string
import threading
import queue
import time
import os

# ================= CONFIGURAÇÕES =================

ctk.set_appearance_mode("dark")

BG = "#080808"
CARD = "#101012"
CARD2 = "#0C0C0E"
RED = "#F01830"
RED_DARK = "#850D20"
WHITE = "#F5F5F7"
MUTED = "#92929F"
GREEN = "#36C78C"
BORDER = "#302027"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_FILE = os.path.join(BASE_DIR, "validos.txt")

events = queue.Queue()
stop_event = threading.Event()
pause_event = threading.Event()
pause_event.set()

running = False
paused = False

total = 0
taken = 0
errors = 0
rate_limits = 0
started_at = None

validos = []
validos_set = set()

if os.path.exists(VALID_FILE):
    with open(VALID_FILE, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name and name not in validos_set:
                validos.append(name)
                validos_set.add(name)


# ================= FUNDO =================

app = ctk.CTk()
app.title("Username Sniper | by 454s")
app.geometry("1660x930")
app.minsize(1100, 780)
app.configure(fg_color=BG)

background = tk.Canvas(
    app,
    highlightthickness=0,
    bd=0,
    bg=BG
)
background.place(x=0, y=0, relwidth=1, relheight=1)

def draw_background(event=None):
    w = max(app.winfo_width(), 1)
    h = max(app.winfo_height(), 1)

    background.delete("all")

    # Fundo preto com degradê vermelho nas extremidades
    for y in range(0, h, 4):
        ratio = y / h
        intensity = int(13 * ratio)

        color = f"#{8 + intensity:02x}0000"
        background.create_rectangle(
            0, y, w, y + 4,
            fill=color,
            outline=color
        )

    # Brilho vermelho inferior
    for i in range(18):
        color_value = max(8, 35 - i * 1.5)
        color = f"#{int(color_value):02x}0000"

        background.create_rectangle(
            0, h - 18 * (i + 1),
            w, h - 18 * i,
            fill=color,
            outline=color
        )

    # Linhas diagonais decorativas
    for x in range(w - 420, w + 100, 95):
        background.create_line(
            x, 0, x - 250, 250,
            fill="#191316",
            width=2
        )

app.bind("<Configure>", draw_background)


# ================= LAYOUT =================

main = ctk.CTkFrame(app, fg_color="transparent")
main.pack(fill="both", expand=True, padx=35, pady=20)

main.grid_columnconfigure(0, weight=1)
main.grid_rowconfigure(3, weight=1)


def make_card(parent, color=CARD, radius=16):
    return ctk.CTkFrame(
        parent,
        fg_color=color,
        corner_radius=radius,
        border_width=1,
        border_color=BORDER
    )


# ================= CABEÇALHO =================

header = ctk.CTkFrame(main, fg_color="transparent")
header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
header.grid_columnconfigure(1, weight=1)

logo = ctk.CTkLabel(
    header,
    text="454s",
    text_color=RED,
    font=("Arial", 30, "bold")
)
logo.grid(row=0, column=0, rowspan=2, padx=(5, 25))

ctk.CTkLabel(
    header,
    text="Dashboard",
    text_color=WHITE,
    font=("Segoe UI", 30, "bold")
).grid(row=0, column=1, sticky="w")

ctk.CTkLabel(
    header,
    text="ROBLOX USERNAME SNIPER   /   BY 454S   /   REAL-TIME OVERVIEW",
    text_color=MUTED,
    font=("Segoe UI", 11, "bold")
).grid(row=1, column=1, sticky="w")

status_badge = ctk.CTkLabel(
    header,
    text="●  IDLE",
    text_color=WHITE,
    fg_color="#211015",
    corner_radius=20,
    width=115,
    height=42,
    font=("Segoe UI", 12, "bold")
)
status_badge.grid(row=0, column=2, rowspan=2, padx=5)


# ================= ESTATÍSTICAS =================

stats = ctk.CTkFrame(main, fg_color="transparent")
stats.grid(row=1, column=0, sticky="ew", pady=(0, 18))

for i in range(4):
    stats.grid_columnconfigure(i, weight=1, uniform="stats")


def create_stat(title, value, accent, icon, col):

    panel = make_card(stats)
    panel.grid(
        row=0, column=col,
        sticky="ew", padx=6
    )

    panel.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        panel,
        text=f"{icon}   {title}",
        text_color=MUTED,
        font=("Segoe UI", 12, "bold")
    ).pack(anchor="w", padx=23, pady=(17, 2))

    label = ctk.CTkLabel(
        panel,
        text=value,
        text_color=accent,
        font=("Segoe UI", 34, "bold")
    )
    label.pack(anchor="w", padx=23, pady=(0, 12))

    return label


available_label = create_stat(
    "AVAILABLE", str(len(validos)), RED, "♟", 0
)

taken_label = create_stat(
    "TAKEN", "0", WHITE, "◇", 1
)

speed_label = create_stat(
    "VALID / S", "0.00", RED, "ϟ", 2
)

errors_label = create_stat(
    "ERRORS", "0", RED, "△", 3
)


# ================= CONFIGURAÇÃO =================

settings = make_card(main)
settings.grid(
    row=2, column=0,
    sticky="ew", pady=(0, 18)
)

setting_inner = ctk.CTkFrame(
    settings,
    fg_color="transparent"
)
setting_inner.pack(fill="x", padx=20, pady=12)

ctk.CTkLabel(
    setting_inner,
    text="▰  USERNAME LENGTH",
    text_color=WHITE,
    font=("Segoe UI", 12, "bold")
).pack(side="left")

length_var = tk.StringVar(value="4")

length_menu = ctk.CTkOptionMenu(
    setting_inner,
    values=[str(i) for i in range(3, 21)],
    variable=length_var,
    width=95,
    height=42,
    fg_color="#171719",
    button_color="#26262A",
    button_hover_color=RED_DARK,
    dropdown_fg_color=CARD
)
length_menu.pack(side="left", padx=25)

ctk.CTkLabel(
    setting_inner,
    text="Random letters and numbers   •   Results saved automatically",
    text_color=MUTED,
    font=("Segoe UI", 12)
).pack(side="left", padx=5)


# ================= PAINÉIS =================

content = ctk.CTkFrame(main, fg_color="transparent")
content.grid(
    row=3, column=0,
    sticky="nsew", pady=(0, 18)
)

content.grid_columnconfigure(0, weight=1, uniform="panels")
content.grid_columnconfigure(1, weight=1, uniform="panels")
content.grid_rowconfigure(0, weight=1)


# ================= PROGRESS =================

progress_panel = make_card(content)
progress_panel.grid(
    row=0, column=0,
    sticky="nsew", padx=(0, 12)
)

progress_inner = ctk.CTkFrame(
    progress_panel,
    fg_color="transparent"
)
progress_inner.pack(
    fill="both", expand=True,
    padx=22, pady=20
)

ctk.CTkLabel(
    progress_inner,
    text="▰  PROGRESS",
    text_color=RED,
    font=("Segoe UI", 14, "bold")
).pack(anchor="w")


# Círculo com antialiasing usando Pillow

circle_label = ctk.CTkLabel(
    progress_inner,
    text=""
)
circle_label.pack(pady=(5, 8))


def create_circle(percent, text, subtext):

    size = 260
    scale = 3
    s = size * scale

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    # Brilho vermelho
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)

    gd.arc(
        (45, 45, s - 45, s - 45),
        start=-90,
        end=-90 + percent * 3.6,
        fill=(255, 20, 50, 200),
        width=13
    )

    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow)

    draw = ImageDraw.Draw(img)

    # Anel de fundo
    margin = 38 * scale

    draw.ellipse(
        (margin, margin, s - margin, s - margin),
        outline="#383038",
        width=14 * scale
    )

    # Anel vermelho
    if percent > 0:
        draw.arc(
            (margin, margin, s - margin, s - margin),
            start=-90,
            end=-90 + percent * 3.6,
            fill=RED,
            width=14 * scale
        )

    img = img.resize(
        (size, size),
        Image.Resampling.LANCZOS
    )

    return ImageTk.PhotoImage(img)


circle_image = None


def update_circle():

    global circle_image

    if running and paused:
        percent = 0
        text = "PAUSED"
    elif running:
        percent = 100
        text = "LIVE"
    else:
        percent = 0
        text = "0%"

    circle_image = create_circle(
        percent,
        text,
        f"{total} checked"
    )

    circle_label.configure(image=circle_image)

    # Texto central separado para ficar nítido
    if not hasattr(update_circle, "center"):
        update_circle.center = ctk.CTkFrame(
            circle_label,
            fg_color="transparent"
        )

    update_circle.center.place(
        relx=0.5, rely=0.5,
        anchor="center"
    )


# Centro do círculo
circle_center = ctk.CTkFrame(
    circle_label,
    fg_color="transparent"
)

circle_center.place(
    relx=0.5, rely=0.5,
    anchor="center"
)

circle_percent = ctk.CTkLabel(
    circle_center,
    text="0%",
    text_color=WHITE,
    font=("Segoe UI", 35, "bold")
)
circle_percent.pack()

circle_checked = ctk.CTkLabel(
    circle_center,
    text="0 checked",
    text_color=MUTED,
    font=("Segoe UI", 12)
)
circle_checked.pack()


# ================= MÉTRICAS =================

metrics = ctk.CTkFrame(
    progress_inner,
    fg_color="transparent"
)
metrics.pack(fill="x", pady=(0, 12))

for i in range(3):
    metrics.grid_columnconfigure(i, weight=1, uniform="metrics")


def create_metric(parent, title, value, col):

    box = make_card(parent, CARD2, 12)

    box.grid(
        row=0, column=col,
        sticky="ew", padx=5
    )

    ctk.CTkLabel(
        box,
        text=title,
        text_color=MUTED,
        font=("Segoe UI", 11)
    ).pack(pady=(13, 3))

    label = ctk.CTkLabel(
        box,
        text=value,
        text_color=WHITE,
        font=("Segoe UI", 18, "bold")
    )
    label.pack(pady=(0, 12))

    return label


elapsed_label = create_metric(
    metrics, "◷   ELAPSED", "00:00:00", 0
)

attempts_label = create_metric(
    metrics, "⟳   ATTEMPTS", "0", 1
)

attempt_rate_label = create_metric(
    metrics, "ϟ   ATTEMPTS / S", "0.00", 2
)


extra_metrics = ctk.CTkFrame(
    progress_inner,
    fg_color="transparent"
)
extra_metrics.pack(fill="x")

extra_metrics.grid_columnconfigure(
    (0, 1), weight=1, uniform="extra"
)

rate_limit_label = create_metric(
    extra_metrics, "♢   RATE LIMITS", "0", 0
)

proxy_label = create_metric(
    extra_metrics, "⌁   PROXY", "OFF", 1
)


# ================= RECENT CAPTURES =================

captures_panel = make_card(content)
captures_panel.grid(
    row=0, column=1,
    sticky="nsew", padx=(12, 0)
)

captures_inner = ctk.CTkFrame(
    captures_panel,
    fg_color="transparent"
)
captures_inner.pack(
    fill="both", expand=True,
    padx=22, pady=20
)

capture_header = ctk.CTkFrame(
    captures_inner,
    fg_color="transparent"
)
capture_header.pack(fill="x", pady=(0, 15))

ctk.CTkLabel(
    capture_header,
    text="▰  RECENT CAPTURES",
    text_color=RED,
    font=("Segoe UI", 14, "bold")
).pack(side="left")

captures_count = ctk.CTkLabel(
    capture_header,
    text=str(len(validos)),
    text_color=GREEN,
    font=("Segoe UI", 14, "bold")
)
captures_count.pack(side="right")


list_frame = ctk.CTkFrame(
    captures_inner,
    fg_color=CARD2,
    corner_radius=12
)
list_frame.pack(
    fill="both", expand=True,
    pady=(0, 12)
)

captures_list = tk.Listbox(
    list_frame,
    bg=CARD2,
    fg=GREEN,
    selectbackground="#69101F",
    selectforeground=WHITE,
    font=("Consolas", 14, "bold"),
    relief="flat",
    bd=0,
    highlightthickness=0,
    activestyle="none"
)

captures_scroll = ctk.CTkScrollbar(
    list_frame,
    orientation="vertical",
    command=captures_list.yview,
    button_color="#51474B",
    button_hover_color=RED
)

captures_list.configure(
    yscrollcommand=captures_scroll.set
)

captures_scroll.pack(side="right", fill="y", padx=5, pady=5)
captures_list.pack(
    side="left", fill="both",
    expand=True, padx=12, pady=10
)


empty_label = ctk.CTkLabel(
    list_frame,
    text="◈\n\nNo captures yet.\nStart searching to find available usernames.",
    text_color=MUTED,
    font=("Segoe UI", 14),
    justify="center"
)

for name in reversed(validos):
    captures_list.insert("end", "     " + name)

if not validos:
    empty_label.place(
        relx=0.5, rely=0.5,
        anchor="center"
    )


# ================= COPIAR =================

copy_row = ctk.CTkFrame(
    captures_inner,
    fg_color="transparent"
)
copy_row.pack(fill="x")


def copy_selected():

    selection = captures_list.curselection()

    if selection:
        value = captures_list.get(
            selection[0]
        ).strip()

        app.clipboard_clear()
        app.clipboard_append(value)

        footer_status.configure(
            text=f"Copied: {value}",
            text_color=GREEN
        )


def copy_all():

    if validos:
        app.clipboard_clear()
        app.clipboard_append("\n".join(validos))

        footer_status.configure(
            text=f"Copied {len(validos)} usernames",
            text_color=GREEN
        )


def clear_results():

    global validos, validos_set

    validos.clear()
    validos_set.clear()

    captures_list.delete(0, "end")

    empty_label.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    available_label.configure(text="0")
    captures_count.configure(text="0")

    with open(VALID_FILE, "w", encoding="utf-8") as f:
        pass

    footer_status.configure(
        text="All results cleared",
        text_color=RED
    )

ctk.CTkButton(
    copy_row,
    text="▢   COPY SELECTED",
    width=175,
    height=43,
    fg_color="transparent",
    border_width=1,
    border_color="#51474B",
    hover_color="#27151A",
    command=copy_selected
).pack(side="left", padx=(0, 12))

ctk.CTkButton(
    copy_row,
    text="▢   COPY ALL",
    width=145,
    height=43,
    fg_color=RED_DARK,
    hover_color=RED,
    command=copy_all
).pack(side="left")
ctk.CTkButton(
    copy_row,
    text="✕   CLEAR ALL",
    width=145,
    height=43,
    fg_color="#241015",
    hover_color="#8B1025",
    border_width=1,
    border_color="#B51B32",
    command=clear_results
).pack(side="left", padx=(12, 0))


# ================= CURRENT TARGET =================

target_panel = make_card(main)
target_panel.grid(
    row=4, column=0,
    sticky="ew", pady=(0, 12)
)

target_inner = ctk.CTkFrame(
    target_panel,
    fg_color="transparent"
)
target_inner.pack(
    fill="x", padx=18, pady=14
)

ctk.CTkLabel(
    target_inner,
    text="▰  CURRENT TARGET",
    text_color=RED,
    font=("Segoe UI", 12, "bold")
).pack(side="left")

target_label = ctk.CTkLabel(
    target_inner,
    text="Idle",
    text_color=WHITE,
    font=("Segoe UI", 14, "bold")
)
target_label.pack(side="right")


# ================= BOTÕES =================

controls = ctk.CTkFrame(
    main,
    fg_color="transparent"
)

controls.grid(
    row=5, column=0,
    sticky="ew"
)


# ================= BUSCA =================

def generate_username(length):

    chars = string.ascii_letters + string.digits

    return "".join(
        random.choices(chars, k=length)
    )


def search_worker(length):

    session = requests.Session()

    while not stop_event.is_set():

        pause_event.wait()

        if stop_event.is_set():
            break

        username = generate_username(length)

        events.put(("target", username))

        try:

            response = session.get(
                "https://auth.roblox.com/v1/usernames/validate",
                params={
                    "Username": username,
                    "Birthday": "2000-01-01"
                },
                timeout=15
            )

            if response.status_code == 429:

                events.put(("rate_limit", None))

                # Respeitar o limite da API
                for _ in range(30):
                    if stop_event.is_set():
                        break
                    if not pause_event.is_set():
                        pause_event.wait()
                    stop_event.wait(1)

                continue

            response.raise_for_status()

            code = response.json().get("code")

            if code == 0:
                events.put(("result", "VALID", username))
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

            elif code == 1:
                events.put(("result", "TAKEN", username))

            elif code == 2:
                events.put(("result", "CENSORED", username))

            else:
                events.put(("error", None))

        except requests.RequestException:
            events.put(("error", None))

        except ValueError:
            events.put(("error", None))


        # Intervalo entre verificações
        stop_event.wait(2.0)

    events.put(("finished", None))


# ================= CONTROLES =================

def start_search():

    global running, paused
    global total, taken, errors, rate_limits
    global started_at

    if running:
        return

    length = int(length_var.get())

    running = True
    paused = False

    total = 0
    taken = 0
    errors = 0
    rate_limits = 0

    started_at = time.time()

    stop_event.clear()
    pause_event.set()

    start_button.configure(state="disabled")
    pause_button.configure(state="normal", text="Ⅱ  PAUSE")
    stop_button.configure(state="normal")

    status_badge.configure(
        text="●  RUNNING",
        text_color=RED
    )

    footer_status.configure(
        text="Search running",
        text_color=GREEN
    )

    threading.Thread(
        target=search_worker,
        args=(length,),
        daemon=True
    ).start()


def pause_search():

    global paused

    if not running:
        return

    if not paused:

        paused = True
        pause_event.clear()

        pause_button.configure(text="▶  RESUME")

        status_badge.configure(
            text="●  PAUSED",
            text_color="#F0B94F"
        )

        footer_status.configure(
            text="Search paused",
            text_color="#F0B94F"
        )

    else:

        paused = False
        pause_event.set()

        pause_button.configure(text="Ⅱ  PAUSE")

        status_badge.configure(
            text="●  RUNNING",
            text_color=RED
        )

        footer_status.configure(
            text="Search resumed",
            text_color=GREEN
        )


def stop_search():

    if running:

        stop_event.set()
        pause_event.set()

        pause_button.configure(state="disabled")
        stop_button.configure(state="disabled")

        status_badge.configure(
            text="●  STOPPING",
            text_color=RED
        )


start_button = ctk.CTkButton(
    controls,
    text="▶   START SEARCH",
    width=210,
    height=50,
    fg_color=RED_DARK,
    hover_color=RED,
    font=("Segoe UI", 13, "bold"),
    command=start_search
)
start_button.pack(side="left", padx=(0, 16))

pause_button = ctk.CTkButton(
    controls,
    text="Ⅱ   PAUSE",
    width=155,
    height=50,
    fg_color="#191719",
    border_width=1,
    border_color="#51474B",
    hover_color="#30262A",
    font=("Segoe UI", 13, "bold"),
    state="disabled",
    command=pause_search
)
pause_button.pack(side="left", padx=(0, 16))

stop_button = ctk.CTkButton(
    controls,
    text="■   STOP",
    width=145,
    height=50,
    fg_color="transparent",
    border_width=1,
    border_color=RED,
    hover_color="#3B1119",
    font=("Segoe UI", 13, "bold"),
    state="disabled",
    command=stop_search
)
stop_button.pack(side="left")


footer_status = ctk.CTkLabel(
    controls,
    text="Ready",
    text_color=MUTED,
    font=("Segoe UI", 11)
)
footer_status.pack(side="right")


# ================= RODAPÉ =================

ctk.CTkLabel(
    main,
    text="USERNAME SNIPER   •   DESIGNED BY 454S   •   SAVED RESULTS: validos.txt",
    text_color="#777078",
    font=("Segoe UI", 10)
).grid(row=6, column=0, sticky="w", pady=(12, 0))


# ================= ATUALIZAÇÃO =================

def update_dashboard():

    global running, paused
    global total, taken, errors, rate_limits

    while not events.empty():

        event = events.get()
        kind = event[0]

        if kind == "target":

            target_label.configure(text=event[1])

        elif kind == "result":

            _, result, username = event

            total += 1

            if result == "VALID":

                if username not in validos_set:

                    validos_set.add(username)
                    validos.append(username)

                    captures_list.insert(
                        0, "     " + username
                    )

                    if empty_label.winfo_manager():
                        empty_label.place_forget()

                    try:
                        with open(
                            VALID_FILE,
                            "a",
                            encoding="utf-8"
                        ) as f:
                            f.write(username + "\n")

                    except OSError:
                        footer_status.configure(
                            text="Could not save results",
                            text_color=RED
                        )

                footer_status.configure(
                    text=f"Available: {username}",
                    text_color=GREEN
                )

            elif result == "TAKEN":
                taken += 1

        elif kind == "error":

            errors += 1

        elif kind == "rate_limit":

            rate_limits += 1

            footer_status.configure(
                text="Rate limit - waiting",
                text_color="#F0B94F"
            )

        elif kind == "finished":

            running = False
            paused = False

            start_button.configure(state="normal")
            pause_button.configure(
                state="disabled",
                text="Ⅱ  PAUSE"
            )
            stop_button.configure(state="disabled")

            status_badge.configure(
                text="●  IDLE",
                text_color=WHITE
            )

            target_label.configure(text="Idle")

            footer_status.configure(
                text="Search stopped",
                text_color=MUTED
            )

    available_label.configure(text=str(len(validos)))
    taken_label.configure(text=str(taken))
    errors_label.configure(text=str(errors))
    captures_count.configure(text=str(len(validos)))

    elapsed = 0

    if started_at:
        elapsed = int(time.time() - started_at)

    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)

    elapsed_label.configure(
        text=f"{hours:02}:{minutes:02}:{seconds:02}"
    )

    attempts_label.configure(text=str(total))

    attempts_per_second = total / max(elapsed, 1)

    attempt_rate_label.configure(
        text=f"{attempts_per_second:.2f}"
    )

    speed_label.configure(
        text=f"{len(validos) / max(elapsed, 1):.2f}"
    )

    rate_limit_label.configure(text=str(rate_limits))

    if running and paused:
        circle_percent.configure(text="PAUSED")
        circle_checked.configure(text=f"{total} checked")

    elif running:
        circle_percent.configure(text="LIVE")
        circle_checked.configure(text=f"{total} checked")

    else:
        circle_percent.configure(text="0%")
        circle_checked.configure(text=f"{total} checked")

    circle_image = create_circle(
        100 if running and not paused else 0,
        "",
        ""
    )

    circle_label.configure(image=circle_image)
    circle_label.image = circle_image

    app.after(200, update_dashboard)


# ================= FECHAR =================

def close_app():

    stop_event.set()
    pause_event.set()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", close_app)

# Primeira imagem do círculo
circle_image = create_circle(0, "", "")
circle_label.configure(image=circle_image)
circle_label.image = circle_image

app.after(200, update_dashboard)

app.mainloop()
