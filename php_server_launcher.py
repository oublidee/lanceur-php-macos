#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lanceur graphique du serveur PHP intégré, pour macOS Apple Silicon.

Démarrage : python3 php_server_launcher.py
Placer index.php à côté de ce fichier, ou choisir un autre routeur dans la fenêtre.
customtkinter est installé au besoin dans un environnement Python isolé adjacent.
L’ancien Tk système est détecté avant ouverture de la fenêtre. Le lanceur
utilise alors Python Homebrew et installe son module python-tk si nécessaire.
Homebrew doit déjà être installé : https://brew.sh/fr/

Le serveur intégré de PHP est destiné au développement local. Le choix 0.0.0.0
le rend accessible depuis le réseau, sous réserve du pare-feu de macOS.
"""

# ─── Paramètres à personnaliser ────────────────────────────────────────────
PORT = 8000
DEFAULT_FILE = "index.php"  # Chemin relatif au script, ou chemin absolu.
HOST = "127.0.0.1"          # 127.0.0.1, 0.0.0.0 ou localhost.
AUTO_OPEN_BROWSER = True
THEME = "blue"             # blue, dark-blue, green, ou fichier JSON de thème.
APPEARANCE_MODE = "dark"   # dark, light ou system.
WINDOW_WIDTH = 980
WINDOW_HEIGHT = 740

import importlib.util
import json
import os
from pathlib import Path
import queue
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
HOST_CHOICES = ("127.0.0.1", "0.0.0.0", "localhost")


def runtime_info(python):
    """Inspecte Python/Tk dans un enfant : ne charge jamais l’ancien Tk ici."""
    code = """
import json, sys
info = {"python": list(sys.version_info[:2]), "tk": None}
try:
    import _tkinter
    info["tk"] = [int(n) for n in _tkinter.TK_VERSION.split(".")]
except ImportError:
    pass
print(json.dumps(info))
"""
    try:
        result = subprocess.run([str(python), "-c", code], capture_output=True,
                                text=True, timeout=15, env=clean_python_environment())
        return json.loads(result.stdout) if result.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def clean_python_environment():
    """Évite de mélanger les bibliothèques de pyenv, d’un venv et de Homebrew."""
    env = os.environ.copy()
    for key in ("PYTHONHOME", "PYTHONPATH", "TCL_LIBRARY", "TK_LIBRARY", "VIRTUAL_ENV"):
        env.pop(key, None)
    return env


def runtime_supported(info):
    return bool(info and info.get("tk") and tuple(info["tk"]) >= (8, 6)
                and tuple(info["python"]) >= (3, 10))


def ensure_supported_python():
    """Sur macOS, remplace Python/Tk système avant toute création de fenêtre."""
    if sys.platform != "darwin" or runtime_supported(runtime_info(sys.executable)):
        return
    print("Le Python actuel ne dispose pas d’un Tk récent compatible. Recherche de Python Homebrew…", flush=True)
    candidates = []
    for prefix in (Path("/opt/homebrew"), Path("/usr/local")):
        candidates.append(prefix / "bin" / "python3")
        candidates.extend(sorted(prefix.glob("opt/python@*/bin/python3.*"), reverse=True))
    usable = []
    for python in candidates:
        # Les fichiers python3.x-config ne sont pas des interpréteurs Python.
        if not python.is_file() or "-config" in python.name:
            continue
        info = runtime_info(python)
        if runtime_supported(info):
            print(f"Utilisation de Python avec Tk {'.'.join(map(str, info['tk']))} : {python}", flush=True)
            os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], clean_python_environment())
        if info and tuple(info["python"]) >= (3, 10):
            usable.append((python, info))
    brew = find_brew()
    if not brew:
        raise RuntimeError("Homebrew est introuvable. Installez-le depuis https://brew.sh/fr/ puis relancez ce fichier.")
    env = brew_environment(brew)
    if not usable:
        print("Installation de Python Homebrew…", flush=True)
        subprocess.run([brew, "install", "python"], check=True, env=env)
        prefix = subprocess.check_output([brew, "--prefix"], text=True, env=env).strip()
        python = Path(prefix) / "bin" / "python3"
        info = runtime_info(python)
        if not info:
            raise RuntimeError(f"Impossible d’inspecter Python Homebrew : {python}")
    else:
        python, info = usable[0]
    formula = "python-tk@" + ".".join(map(str, info["python"]))
    print(f"Installation du module graphique compatible : brew install {formula}", flush=True)
    subprocess.run([brew, "install", formula], check=True, env=env)
    if not runtime_supported(runtime_info(python)):
        raise RuntimeError(f"Tk reste indisponible avec {python}. Vérifiez l’installation de {formula}.")
    os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], clean_python_environment())


def load_interface():
    """Installe uniquement la dépendance manquante, sans modifier Python global."""
    try:
        import tkinter
    except ImportError as exc:
        raise RuntimeError(
            "Tkinter est absent de ce Python. Installez une distribution Python "
            "avec Tk, ou la formule Homebrew python-tk correspondant à sa version."
        ) from exc
    if importlib.util.find_spec("customtkinter") is None:
        if os.environ.get("PHP_LAUNCHER_BOOTSTRAPPED") == "1":
            raise RuntimeError("customtkinter reste introuvable après installation.")
        import venv
        # Une ancienne copie du venv peut encore utiliser le Tk système 8.5.
        environment = SCRIPT_DIR / f".venv-php-launcher-{sys.version_info.major}.{sys.version_info.minor}"
        python = environment / "bin" / "python"
        # Réutiliser l’installation locale lors des lancements suivants.
        installed = python.is_file() and runtime_supported(runtime_info(python)) and subprocess.run(
            [str(python), "-c", "import tkinter, customtkinter"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0
        if not installed:
            print("Installation de l’interface dans", environment, flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
            subprocess.run(
                [str(python), "-m", "pip", "install", "customtkinter"], check=True
            )
        env = clean_python_environment()
        env["PHP_LAUNCHER_BOOTSTRAPPED"] = "1"
        os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], env)
    import customtkinter
    return customtkinter


def stop_process(process):
    """Termine le groupe enfant, puis le tue si l’arrêt dépasse trois secondes."""
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)
    except ProcessLookupError:
        pass


def brew_environment(brew):
    """Finder ne fournit pas forcément le PATH du Terminal : on le complète."""
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([
        str(Path(brew).parent), "/opt/homebrew/bin", "/opt/homebrew/sbin",
        "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin",
        env.get("PATH", ""),
    ])
    env["HOMEBREW_NO_AUTO_UPDATE"] = "1"  # Une mise à jour explicite par contrôle.
    env["HOMEBREW_NO_ENV_HINTS"] = "1"
    # PHP_CLI_SERVER_WORKERS pourrait créer plusieurs serveurs à notre insu.
    env.pop("PHP_CLI_SERVER_WORKERS", None)
    return env


def find_brew():
    candidates = ["/opt/homebrew/bin/brew", "/usr/local/bin/brew", shutil.which("brew")]
    return next((p for p in candidates if p and os.access(p, os.X_OK)), None)


def main():
    ctk = load_interface()
    from tkinter import filedialog

    ctk.set_appearance_mode(APPEARANCE_MODE)
    ctk.set_default_color_theme(THEME)

    class Launcher(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Lanceur PHP")
            self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
            self.minsize(820, 650)
            self.events = queue.Queue()
            self.cancelled = threading.Event()
            self.process_lock = threading.Lock()
            self.command_process = None
            self.server_process = None
            self.php = None
            self.env = None
            self.ready = False
            self.starting = False
            self.stopping = False
            self.closing = False
            self.server_url = None
            self.selected_file = Path(DEFAULT_FILE).expanduser()
            if not self.selected_file.is_absolute():
                self.selected_file = SCRIPT_DIR / self.selected_file
            self.build_ui()
            self.protocol("WM_DELETE_WINDOW", self.close)
            self.after(80, self.drain_events)
            self.check_environment()

        def build_ui(self):
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(2, weight=1)
            header = ctk.CTkFrame(self, corner_radius=14)
            header.grid(row=0, column=0, padx=24, pady=(24, 16), sticky="ew")
            header.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(header, text="Lanceur PHP", font=ctk.CTkFont(size=27, weight="bold")).grid(
                row=0, column=0, padx=20, pady=(18, 2), sticky="w")
            ctk.CTkLabel(header, text="Votre environnement de développement local").grid(
                row=1, column=0, padx=20, pady=(0, 18), sticky="w")
            self.badge = ctk.CTkLabel(header, text="●  Arrêté", corner_radius=12,
                                      fg_color="#374151", text_color="white", width=130, height=34)
            self.badge.grid(row=0, column=1, rowspan=2, padx=20)

            settings = ctk.CTkFrame(self, corner_radius=14)
            settings.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="ew")
            settings.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(settings, text="Fichier PHP utilisé comme routeur", anchor="w").grid(
                row=0, column=0, columnspan=3, padx=20, pady=(15, 5), sticky="w")
            self.file_text = ctk.StringVar(value=str(self.selected_file))
            self.file_entry = ctk.CTkEntry(settings, textvariable=self.file_text, height=38, corner_radius=10)
            self.file_entry.grid(row=1, column=0, columnspan=2, padx=(20, 12), sticky="ew")
            self.file_entry.configure(state="readonly")
            self.choose_button = ctk.CTkButton(settings, text="Choisir un fichier…", corner_radius=10,
                                               height=38, command=self.choose_file)
            self.choose_button.grid(row=1, column=2, padx=(0, 20))

            controls = ctk.CTkFrame(settings, fg_color="transparent")
            controls.grid(row=2, column=0, columnspan=3, padx=20, pady=15, sticky="ew")
            ctk.CTkLabel(controls, text="Hôte").grid(row=0, column=0, padx=(0, 10))
            self.host = ctk.StringVar(value=HOST if HOST in HOST_CHOICES else HOST_CHOICES[0])
            self.host_menu = ctk.CTkOptionMenu(controls, values=list(HOST_CHOICES), variable=self.host,
                                               corner_radius=10, width=150)
            self.host_menu.grid(row=0, column=1, padx=(0, 20))
            ctk.CTkLabel(controls, text="Port").grid(row=0, column=2, padx=(0, 10))
            self.port = ctk.StringVar(value=str(PORT))
            self.port_entry = ctk.CTkEntry(controls, textvariable=self.port, width=80, corner_radius=10)
            self.port_entry.grid(row=0, column=3, padx=(0, 20))
            self.auto_open = ctk.BooleanVar(value=AUTO_OPEN_BROWSER)
            self.browser_check = ctk.CTkCheckBox(controls, text="Ouvrir le navigateur", variable=self.auto_open)
            self.browser_check.grid(row=0, column=4)

            actions = ctk.CTkFrame(settings, fg_color="transparent")
            actions.grid(row=3, column=0, columnspan=3, padx=20, pady=(0, 18), sticky="ew")
            self.toggle_button = ctk.CTkButton(actions, text="Vérification en cours…", height=42,
                corner_radius=12, width=230, command=self.toggle, state="disabled")
            self.toggle_button.pack(side="left")
            self.open_button = ctk.CTkButton(actions, text="Ouvrir", height=42, width=95,
                corner_radius=12, command=self.open_browser, state="disabled")
            self.open_button.pack(side="left", padx=12)
            self.retry_button = ctk.CTkButton(actions, text="Revérifier", height=42, width=110,
                corner_radius=12, command=self.check_environment, state="disabled")
            self.retry_button.pack(side="right")

            logs = ctk.CTkFrame(self, corner_radius=14)
            logs.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="nsew")
            logs.grid_columnconfigure(0, weight=1)
            logs.grid_rowconfigure(1, weight=1)
            ctk.CTkLabel(logs, text="Journal en temps réel", font=ctk.CTkFont(size=15, weight="bold")).grid(
                row=0, column=0, padx=18, pady=12, sticky="w")
            ctk.CTkButton(logs, text="Effacer", width=85, corner_radius=10, command=self.clear_logs).grid(
                row=0, column=1, padx=18, pady=12)
            self.log_box = ctk.CTkTextbox(logs, corner_radius=10, font=ctk.CTkFont(family="Menlo", size=12),
                                           wrap="word", state="disabled")
            self.log_box.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 14), sticky="nsew")
            self.footer = ctk.CTkLabel(self, text="Préparation de Homebrew et PHP…", anchor="w")
            self.footer.grid(row=3, column=0, padx=26, pady=(0, 14), sticky="ew")

        def log(self, text):
            # Les threads ne touchent jamais directement aux widgets Tk.
            stamp = datetime.now().strftime("%H:%M:%S")
            self.events.put(("log", f"[{stamp}] {text}"))

        def clear_logs(self):
            self.log_box.configure(state="normal")
            self.log_box.delete("1.0", "end")
            self.log_box.configure(state="disabled")

        def drain_events(self):
            # Le quota préserve la réactivité même avec beaucoup de requêtes PHP.
            for _ in range(250):
                try:
                    kind, value = self.events.get_nowait()
                except queue.Empty:
                    break
                if kind == "log":
                    self.log_box.configure(state="normal")
                    self.log_box.insert("end", value + "\n")
                    if int(self.log_box.index("end-1c").split(".")[0]) > 6000:
                        self.log_box.delete("1.0", "1001.0")
                    self.log_box.see("end")
                    self.log_box.configure(state="disabled")
                elif kind == "environment":
                    self.ready = value
                    self.retry_button.configure(state="normal")
                    self.toggle_button.configure(state="normal" if value else "disabled", text="Démarrer le serveur")
                    self.footer.configure(text="Environnement prêt" if value else "Préparation impossible — consultez le journal")
                elif kind == "running":
                    self.starting = False
                    self.server_url = value
                    self.badge.configure(text="●  En cours", fg_color="#166534")
                    self.toggle_button.configure(text="Arrêter le serveur", state="normal",
                                                 fg_color="#b91c1c", hover_color="#991b1b")
                    self.open_button.configure(state="normal")
                    self.footer.configure(text=value)
                    if self.auto_open.get():
                        self.open_browser()
                elif kind == "stopped":
                    self.starting = self.stopping = False
                    self.server_url = None
                    self.badge.configure(text="●  Arrêté", fg_color="#374151")
                    self.toggle_button.configure(text="Démarrer le serveur", state="normal" if self.ready else "disabled",
                                                 fg_color="#2563eb", hover_color="#1d4ed8")
                    self.open_button.configure(state="disabled")
                    self.set_settings_enabled(True)
                    self.retry_button.configure(state="normal")
                    self.footer.configure(text="Serveur arrêté")
                elif kind == "closed":
                    self.destroy()
                    return
            self.after(80, self.drain_events)

        def run_command(self, args):
            """Capture aussi stderr pour afficher les opérations Homebrew en direct."""
            if self.cancelled.is_set():
                raise RuntimeError("Préparation annulée.")
            with self.process_lock:
                if self.cancelled.is_set():
                    raise RuntimeError("Préparation annulée.")
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", env=self.env,
                    bufsize=1, start_new_session=True)
                self.command_process = process
            lines = []
            try:
                for line in process.stdout:
                    line = line.rstrip()
                    lines.append(line)
                    if line:
                        self.log(line)
                code = process.wait()
                if code:
                    raise RuntimeError(f"Échec de {' '.join(args)} (code {code}).")
                return "\n".join(lines)
            finally:
                process.stdout.close()
                with self.process_lock:
                    self.command_process = None

        def check_environment(self):
            self.ready = False
            self.toggle_button.configure(state="disabled", text="Vérification en cours…")
            self.retry_button.configure(state="disabled")
            self.footer.configure(text="Préparation de Homebrew et PHP…")
            threading.Thread(target=self.prepare_environment, daemon=True).start()

        def prepare_environment(self):
            try:
                brew = find_brew()
                if not brew:
                    raise RuntimeError("Homebrew est introuvable. Installez-le depuis https://brew.sh/fr/ puis cliquez sur Revérifier.")
                self.env = brew_environment(brew)
                self.log(f"Homebrew trouvé : {brew}")
                self.log("Mise à jour de Homebrew : brew update (cela peut prendre plusieurs minutes)…")
                self.run_command([brew, "update"])
                self.log("Recherche d’une installation PHP gérée par Homebrew…")
                installed = self.run_command([brew, "list", "--formula", "--versions"])
                formulas = [line.split()[0] for line in installed.splitlines() if line.split()]
                versions = sorted((f for f in formulas if f.startswith("php@")),
                                  key=lambda f: tuple(int(n) for n in f[4:].split(".")), reverse=True)
                formula = "php" if "php" in formulas else next(iter(versions), None)
                if formula is None:
                    self.log("PHP n’est pas installé : installation automatique avec brew install php…")
                    self.run_command([brew, "install", "php"])
                    formula = "php"
                prefix = self.run_command([brew, "--prefix", formula]).strip().splitlines()[-1]
                php = Path(prefix) / "bin" / "php"
                if not php.is_file() or not os.access(php, os.X_OK):
                    raise RuntimeError(f"Binaire PHP Homebrew introuvable ou inexécutable : {php}")
                self.php = str(php)
                self.log(f"Binaire PHP sélectionné : {self.php}")
                self.run_command([self.php, "--version"])
                self.log("🎉 Tout est OK – environnement prêt")
                self.events.put(("environment", True))
            except Exception as exc:
                if not self.cancelled.is_set():
                    self.log(f"Erreur : {exc}")
                    self.events.put(("environment", False))

        def choose_file(self):
            chosen = filedialog.askopenfilename(title="Choisir le routeur PHP",
                initialdir=str(self.selected_file.parent), filetypes=[("Fichiers PHP", "*.php")])
            if chosen:
                self.selected_file = Path(chosen)
                self.file_text.set(chosen)
                self.log(f"Routeur sélectionné : {chosen}")

        def set_settings_enabled(self, enabled):
            state = "normal" if enabled else "disabled"
            for widget in (self.choose_button, self.host_menu, self.port_entry, self.browser_check):
                widget.configure(state=state)

        def toggle(self):
            if self.starting or self.stopping or self.closing:
                return
            if self.server_process is not None:
                self.stopping = True
                self.toggle_button.configure(text="Arrêt en cours…", state="disabled")
                self.open_button.configure(state="disabled")
                self.log("Arrêt du serveur demandé…")
                threading.Thread(target=stop_process, args=(self.server_process,), daemon=True).start()
                return
            if not self.ready:
                return
            try:
                raw_port = self.port.get().strip()
                if not raw_port.isascii() or not raw_port.isdecimal():
                    raise ValueError("Le port doit être un nombre entier entre 1 et 65535.")
                port = int(raw_port)
                if not 1 <= port <= 65535:
                    raise ValueError("Le port doit être compris entre 1 et 65535.")
                router = self.selected_file.resolve()
                if router.suffix.lower() != ".php" or not router.is_file():
                    raise ValueError(f"Fichier PHP introuvable : {router}. Utilisez « Choisir un fichier… ».")
                if not os.access(router, os.R_OK):
                    raise ValueError(f"Le fichier PHP n’est pas lisible : {router}")
                host = self.host.get()
                # Vérification préalable ; PHP reste l’autorité en cas de course.
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                    probe.bind((host, port))
            except (ValueError, OSError) as exc:
                self.log(f"Impossible de démarrer : {exc}")
                return
            self.starting = True
            self.set_settings_enabled(False)
            self.retry_button.configure(state="disabled")
            self.toggle_button.configure(text="Démarrage en cours…", state="disabled")
            threading.Thread(target=self.serve, args=(host, port, router), daemon=True).start()

        def serve(self, host, port, router):
            process = None
            try:
                args = [self.php, "-S", f"{host}:{port}", "-t", str(router.parent), str(router)]
                self.log(f"Démarrage sur {host}:{port} — routeur : {router}")
                with self.process_lock:
                    if self.cancelled.is_set():
                        return
                    process = subprocess.Popen(args, cwd=str(router.parent), env=self.env,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                        encoding="utf-8", errors="replace", bufsize=1, start_new_session=True)
                    self.server_process = process
                # Lecture dédiée : la disponibilité du serveur est contrôlée en parallèle.
                def read_output():
                    for line in process.stdout:
                        if line.strip():
                            self.log(line.rstrip())
                reader = threading.Thread(target=read_output, daemon=True)
                reader.start()
                browser_host = "127.0.0.1" if host == "0.0.0.0" else host
                deadline = time.monotonic() + 8
                while process.poll() is None and not self.cancelled.is_set():
                    try:
                        with socket.create_connection((browser_host, port), timeout=0.25):
                            pass
                        if process.poll() is None:
                            self.events.put(("running", f"http://{browser_host}:{port}/"))
                        break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Le serveur ne répond pas après huit secondes.")
                        self.cancelled.wait(0.1)
                code = process.wait()
                reader.join(timeout=1)
                if not self.cancelled.is_set():
                    self.log(f"Serveur arrêté (code {code}).")
            except Exception as exc:
                self.log(f"Erreur du serveur : {exc}")
                stop_process(process)
            finally:
                if process is not None and process.stdout is not None:
                    process.stdout.close()
                with self.process_lock:
                    self.server_process = None
                self.events.put(("stopped", None))

        def open_browser(self):
            if not self.server_url or self.server_process is None or self.server_process.poll() is not None:
                return
            url = self.server_url
            def open_url():
                try:
                    if webbrowser.open(url):
                        self.log(f"Ouverture du navigateur : {url}")
                    else:
                        self.log(f"Navigateur indisponible. Ouvrez cette adresse : {url}")
                except Exception as exc:
                    self.log(f"Impossible d’ouvrir le navigateur : {exc}")
            threading.Thread(target=open_url, daemon=True).start()

        def close(self):
            if self.closing:
                return
            self.closing = True
            self.cancelled.set()
            self.toggle_button.configure(state="disabled", text="Fermeture…")
            self.retry_button.configure(state="disabled")
            self.open_button.configure(state="disabled")
            self.set_settings_enabled(False)
            self.log("Fermeture : arrêt des processus en cours…")
            def cleanup():
                try:
                    with self.process_lock:
                        processes = (self.server_process, self.command_process)
                    for process in processes:
                        stop_process(process)
                finally:
                    self.events.put(("closed", None))
            threading.Thread(target=cleanup, daemon=True).start()

    Launcher().mainloop()


if __name__ == "__main__":
    try:
        ensure_supported_python()
        main()
    except Exception as error:
        print(f"Impossible de lancer l’application : {error}", file=sys.stderr)
        sys.exit(1)
