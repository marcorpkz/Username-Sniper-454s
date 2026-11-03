
import tkinter as tk
from tkinter import ttk
import requests
import random
import string
import threading
import queue
import time
import os
import sys



if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VALID_FILE = os.path.join(BASE_DIR, "validos.txt")



BG = "#10141F"
PANEL = "#191F2E"
PANEL2 = "#20283A"
BLUE = "#4389FF"
GREEN = "#35D399"
RED = "#F05B67"
WHITE = "#F1F5F9"
GRAY = "#8994A8"
YELLOW = "#F5C451"



events = queue.Queue()
stop_event = threading.Event()
pause_event = threading.Event()
pause_event.set()

running = False
paused = False
worker = None

total = 0
available = 0
taken = 0
censored = 0

validos = []
validos_set = set()


def generate_username(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def check_username(username):
    url = "https://auth.roblox.com/v1/usernames/validate"

    params = {
        "Username": username,
        "Birthday": "2000-01-01"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json().get("code")


def search_worker(length):
    global validos_set

    session = requests.Session()

    while not stop_event.is_set():

        if not pause_event.wait(timeout=0.2):
            continue

        username = generate_username(length)

        try:
            code = check_username(username)

            if code == 0:
                if username not in validos_set:
                    validos_set.add(username)
                    validos.append(username)

                    with open(VALID_FILE, "a", encoding="utf-8") as f:
                        f.write(username + "\n")

                events.put(("result", "VALID", username))

            elif code == 1:
                events.put(("result", "TAKEN", username))

            elif code == 2:
                events.put(("result", "CENSORED", username))

            else:
                events.put(("result", "UNKNOWN", username))

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                events.put(("log", "Limite de consultas atingido. Aguardando..."))
                stop_event.wait(10)
            else:
                events.put(("log", f"Erro HTTP: {e}"))

        except requests.exceptions.RequestException as e:
            events.put(("log", f"Erro de conexão: {e}"))

        time.sleep(1)

    events.put(("finished", None, None))



root = tk.Tk()
root.title("Roblox Username Sniper")
root.geometry("900x650")
root.minsize(800, 580)
root.configure(bg=BG)



style = ttk.Style()
style.theme_use("clam")

style.configure(
    "TCombobox",
    fieldbackground=PANEL2,
    background=PANEL2,
    foreground=WHITE,
    arrowcolor=WHITE
)



header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=30, pady=(25, 15))

tk.Label(
    header,
    text="USERNAME SNIPER",
    bg=BG,
    fg=WHITE,
    font=("Segoe UI", 23, "bold")
).pack(anchor="w")

tk.Label(
    header,
    text="ROBLOX USERNAME CHECKER",
    bg=BG,
    fg=BLUE,
    font=("Segoe UI", 9, "bold")
).pack(anchor="w")



config = tk.Frame(root, bg=PANEL, padx=20, pady=18)
config.pack(fill="x", padx=30, pady=10)

tk.Label(
    config,
    text="CONFIGURAÇÃO",
    bg=PANEL,
    fg=GRAY,
    font=("Segoe UI", 9, "bold")
).pack(anchor="w")

row = tk.Frame(config, bg=PANEL)
row.pack(fill="x", pady=(12, 0))

tk.Label(
    row,
    text="Tamanho do username:",
    bg=PANEL,
    fg=WHITE,
    font=("Segoe UI", 10)
).pack(side="left")

length_var = tk.StringVar(value="5")

length_box = ttk.Combobox(
    row,
    textvariable=length_var,
    values=[str(i) for i in range(1, 21)],
    state="readonly",
    width=7
)
length_box.pack(side="left", padx=12)



stats = tk.Frame(root, bg=BG)
stats.pack(fill="x", padx=30, pady=10)


def create_stat(parent, title, color):
    frame = tk.Frame(parent, bg=PANEL, padx=15, pady=15)

    tk.Label(
        frame,
        text=title,
        bg=PANEL,
        fg=GRAY,
        font=("Segoe UI", 9, "bold")
    ).pack(anchor="w")

    value = tk.Label(
        frame,
        text="0",
        bg=PANEL,
        fg=color,
        font=("Segoe UI", 25, "bold")
    )
    value.pack(anchor="w")

    return frame, value


stat1, total_label = create_stat(stats, "VERIFICADOS", WHITE)
stat2, valid_label = create_stat(stats, "DISPONÍVEIS", GREEN)
stat3, taken_label = create_stat(stats, "OCUPADOS", RED)
stat4, censored_label = create_stat(stats, "CENSURADOS", YELLOW)

for frame in (stat1, stat2, stat3, stat4):
    frame.pack(side="left", expand=True, fill="x", padx=5)



buttons = tk.Frame(root, bg=BG)
buttons.pack(fill="x", padx=30, pady=15)


def make_button(parent, text, color, command):
    return tk.Button(
        parent,
        text=text,
        bg=color,
        fg=WHITE,
        activebackground=color,
        activeforeground=WHITE,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        bd=0,
        padx=20,
        pady=11,
        cursor="hand2",
        command=command
    )



history_panel = tk.Frame(root, bg=PANEL, padx=15, pady=15)
history_panel.pack(fill="both", expand=True, padx=30, pady=(5, 20))

history_header = tk.Frame(history_panel, bg=PANEL)
history_header.pack(fill="x")

tk.Label(
    history_header,
    text="HISTÓRICO DE BUSCA",
    bg=PANEL,
    fg=WHITE,
    font=("Segoe UI", 10, "bold")
).pack(side="left")

status_label = tk.Label(
    history_header,
    text="● PARADO",
    bg=PANEL,
    fg=GRAY,
    font=("Segoe UI", 9, "bold")
)
status_label.pack(side="right")


history = tk.Text(
    history_panel,
    bg="#111722",
    fg=WHITE,
    insertbackground=WHITE,
    font=("Consolas", 10),
    relief="flat",
    bd=0,
    padx=12,
    pady=12,
    state="disabled"
)
history.pack(fill="both", expand=True, pady=(12, 0))

history.tag_config("VALID", foreground=GREEN)
history.tag_config("TAKEN", foreground=RED)
history.tag_config("CENSORED", foreground=YELLOW)
history.tag_config("UNKNOWN", foreground=GRAY)
history.tag_config("INFO", foreground=BLUE)


def add_history(message, tag="INFO"):
    history.config(state="normal")
    history.insert("end", message + "\n", tag)
    history.see("end")
    history.config(state="disabled")





def start_search():
    global running, paused, worker

    if running:
        return

    try:
        length = int(length_var.get())
    except ValueError:
        return

    running = True
    paused = False

    stop_event.clear()
    pause_event.set()

    start_button.config(state="disabled")
    pause_button.config(state="normal", text="PAUSAR")
    stop_button.config(state="normal")

    status_label.config(text="● PROCURANDO", fg=GREEN)

    add_history(f"Iniciando busca com {length} caracteres...")

    worker = threading.Thread(
        target=search_worker,
        args=(length,),
        daemon=True
    )
    worker.start()


def pause_search():
    global paused

    if not running:
        return

    if not paused:
        paused = True
        pause_event.clear()

        pause_button.config(text="CONTINUAR")
        status_label.config(text="● PAUSADO", fg=YELLOW)

        add_history("Busca pausada.")

    else:
        paused = False
        pause_event.set()

        pause_button.config(text="PAUSAR")
        status_label.config(text="● PROCURANDO", fg=GREEN)

        add_history("Busca retomada.")


def stop_search():
    global paused

    if not running:
        return

    stop_event.set()
    pause_event.set()

    paused = False
    pause_button.config(state="disabled")
    stop_button.config(state="disabled")

    status_label.config(text="● ENCERRANDO", fg=YELLOW)

    add_history("Encerrando busca...")


def update_results():
    global total, available, taken, censored
    global running

    while not events.empty():

        event = events.get()
        kind = event[0]

        if kind == "result":
            _, result, username = event

            total += 1

            if result == "VALID":
                available += 1

            elif result == "TAKEN":
                taken += 1

            elif result == "CENSORED":
                censored += 1

            total_label.config(text=str(total))
            valid_label.config(text=str(available))
            taken_label.config(text=str(taken))
            censored_label.config(text=str(censored))

            add_history(f"[{result}] {username}", result)

        elif kind == "log":
            add_history(event[1])

        elif kind == "finished":
            running = False

            start_button.config(state="normal")
            pause_button.config(state="disabled", text="PAUSAR")
            stop_button.config(state="disabled")

            status_label.config(text="● PARADO", fg=GRAY)

            add_history("Busca finalizada.")
            add_history(f"Total de disponíveis: {available}")

    root.after(100, update_results)


def close_app():
    stop_event.set()
    pause_event.set()
    root.destroy()



start_button = make_button(
    buttons, "INICIAR BUSCA", BLUE, start_search
)
start_button.pack(side="left", padx=(0, 8))

pause_button = make_button(
    buttons, "PAUSAR", PANEL2, pause_search
)
pause_button.pack(side="left", padx=8)
pause_button.config(state="disabled")

stop_button = make_button(
    buttons, "PARAR", RED, stop_search
)
stop_button.pack(side="left", padx=8)
stop_button.config(state="disabled")


tk.Label(
    root,
    text="Os resultados disponíveis são salvos automaticamente em validos.txt",
    bg=BG,
    fg=GRAY,
    font=("Segoe UI", 8)
).pack(pady=(0, 12))


root.protocol("WM_DELETE_WINDOW", close_app)

update_results()
root.mainloop()
