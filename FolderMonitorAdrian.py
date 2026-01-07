import os, sys, json, time, smtplib, logging, zipfile, shutil, threading, webbrowser
from pathlib import Path
from datetime import datetime, timezone
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from email import encoders
from email.mime.text import MIMEText

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# tray icon
import pystray
from PIL import Image, ImageDraw

# ---------- helpers ----------
def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def setup_logger(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )

def bytes_to_mb(b: int) -> float:
    return round(b / (1024 * 1024), 2)

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def resolve_relative_to_base(raw_path: str, base: Path) -> Path:
    p = Path(raw_path)
    return p if p.is_absolute() else (base / p).resolve()

def attach_file(msg: MIMEMultipart, path: Path):
    part = MIMEBase("application", "octet-stream")
    with open(path, "rb") as f:
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
    msg.attach(part)

def send_mail(smtp_cfg: dict, subject: str, body: str, attachments: list[Path]):
    msg = MIMEMultipart()
    msg["From"] = smtp_cfg["from_addr"]
    msg["To"] = ", ".join(smtp_cfg["to_addrs"])
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    for a in attachments:
        attach_file(msg, a)
    with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"]) as server:
        if smtp_cfg.get("use_starttls", True):
            server.starttls()
        if smtp_cfg.get("username"):
            server.login(smtp_cfg["username"], smtp_cfg["password"])
        server.send_message(msg)

def make_zip_of_files(files, tmp_dir: Path) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / f"payload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    staging = tmp_dir / f"staging_{int(time.time())}"
    staging.mkdir()
    try:
        for f in files:
            shutil.copy2(f, staging / f.name)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f in staging.iterdir():
                zf.write(f, arcname=f.name)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return zip_path

def is_file_ready(path: Path) -> bool:
    try:
        with open(path, "rb"):
            pass
        fd = os.open(str(path), os.O_RDONLY)
        os.close(fd)
        return True
    except Exception:
        return False

# ---------- core sender ----------
class ImmediateSender:
    def __init__(self, cfg: dict, base: Path, state_path: Path, include_ext, exclude_ext, min_age: int):
        self.cfg = cfg
        self.base = base
        self.state_path = state_path
        self.include_ext = include_ext
        self.exclude_ext = exclude_ext
        self.min_age = min_age
        self.watch = Path(cfg["watch_folder"])
        self.backup = Path(cfg["backup_folder"])
        self.max_mb = float(cfg.get("max_total_attachment_mb", 18))
        self.zip_before = bool(cfg.get("zip_before_email", False))

        if state_path.exists():
            try:
                self.state = json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                self.state = {}
        else:
            self.state = {}
        self.state.setdefault("processed_files", [])

        for d in (self.watch, self.backup, self.state_path.parent):
            Path(d).mkdir(parents=True, exist_ok=True)

        self._pending = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._paused = False

        self._sweeper = threading.Thread(target=self._sweep_loop, daemon=True)
        self._sweeper.start()

    def stop(self):
        self._stop.set()
        self._sweeper.join(timeout=3)

    def toggle_pause(self):
        self._paused = not self._paused
        return self._paused

    @property
    def paused(self):
        return self._paused

    def on_touch(self, full_path: str):
        if self._paused:
            return
        p = Path(full_path)
        if not p.exists() or not p.is_file():
            return
        ext = p.suffix.lower()
        if self.include_ext and ext not in self.include_ext:
            return
        if self.exclude_ext and ext in self.exclude_ext:
            return
        with self._lock:
            self._pending[str(p)] = time.time()

    def _sweep_loop(self):
        while not self._stop.is_set():
            if self._paused:
                time.sleep(0.5)
                continue
            now = time.time()
            to_process = []
            with self._lock:
                for path_str, _ in list(self._pending.items()):
                    p = Path(path_str)
                    try:
                        if not p.exists():
                            self._pending.pop(path_str, None)
                            continue
                        age_ok = (now - p.stat().st_mtime) >= self.min_age
                        if age_ok and is_file_ready(p):
                            to_process.append(p)
                            self._pending.pop(path_str, None)
                    except Exception:
                        pass
            if to_process:
                try:
                    self._process_files(to_process)
                except Exception as e:
                    logging.error(f"Processing error: {e}")
            time.sleep(1)

    def _process_files(self, files):
        total_bytes = sum(p.stat().st_size for p in files)
        total_mb = bytes_to_mb(total_bytes)
        temp_to_cleanup = []

        if self.zip_before or (self.max_mb > 0 and total_mb > self.max_mb):
            tmp_dir = Path(os.getenv("TEMP", str(self.state_path.parent)))
            zip_path = make_zip_of_files(files, tmp_dir)
            attachments = [zip_path]
            temp_to_cleanup.append(zip_path)
            body_list = "\n".join(f" - {p.name}" for p in files)
            logging.info(f"Created ZIP: {zip_path} ({bytes_to_mb(zip_path.stat().st_size)} MB)")
        else:
            attachments = files
            body_list = "\n".join(f" - {p.name} ({bytes_to_mb(p.stat().st_size)} MB)" for p in files)

        subject = f'{self.cfg["smtp"].get("subject_prefix","[FolderMonitorAdrian]")} {len(files)} new file(s)'
        body = (
            f"The following files were detected in '{self.watch}':\n\n"
            f"{body_list}\n\n"
            f"Total size: {total_mb} MB\n"
            "This email was generated automatically by FolderMonitorAdrian."
        )

        try:
            send_mail(self.cfg["smtp"], subject, body, attachments)
            logging.info(f"Email sent for {len(files)} file(s).")
        finally:
            for t in temp_to_cleanup:
                try:
                    t.unlink(missing_ok=True)
                except Exception:
                    pass

        for f in files:
            try:
                dest = self.backup / f.name
                if dest.exists():
                    stem, suff = dest.stem, dest.suffix
                    dest = self.backup / f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suff}"
                shutil.move(str(f), str(dest))
                logging.info(f"Moved: {f} -> {dest}")
                if str(f) not in self.state["processed_files"]:
                    self.state["processed_files"].append(str(f))
            except Exception as e:
                logging.error(f"Move to backup failed for {f}: {e}")

        self.state["last_run_utc"] = datetime.now(timezone.utc).isoformat()
        save_json(self.state, self.state_path)

# ---------- events ----------
class Handler(FileSystemEventHandler):
    def __init__(self, sender: ImmediateSender):
        super().__init__()
        self.sender = sender
    def on_created(self, e):  # file dropped/created
        if not e.is_directory: self.sender.on_touch(e.src_path)
    def on_modified(self, e): # file still writing
        if not e.is_directory: self.sender.on_touch(e.src_path)
    def on_moved(self, e):    # temp->final rename
        if not e.is_directory: self.sender.on_touch(e.dest_path)

# ---------- tray icon ----------
def load_icon_image(base: Path) -> Image.Image:
    ico_file = base / "foldermonitoradrian.ico"
    if ico_file.exists():
        # PIL can open .ico directly
        return Image.open(ico_file)
    # fallback: generate a simple badge
    img = Image.new("RGBA", (64, 64), (40, 120, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 20, 56, 44], outline=(255, 255, 255, 255), width=3)
    d.rectangle([12, 24, 52, 40], fill=(255, 255, 255, 255))
    return img

# ---------- main ----------
def main():
    base = get_base_dir()
    cfg = load_json(base / "config.json")
    state_path = resolve_relative_to_base(cfg["state_file"], base)
    log_path   = resolve_relative_to_base(cfg["log_file"], base)

    include_ext = [e.lower() for e in cfg.get("include_extensions", [])]
    exclude_ext = [e.lower() for e in cfg.get("exclude_extensions", [])]
    min_age = int(cfg.get("min_file_age_seconds", 5))

    setup_logger(log_path)
    logging.info("Starting FolderMonitorAdrian (instant + tray)")

    sender = ImmediateSender(cfg, base, state_path, include_ext, exclude_ext, min_age)

    watch_path = Path(cfg["watch_folder"]); watch_path.mkdir(parents=True, exist_ok=True)
    observer = Observer(); observer.schedule(Handler(sender), str(watch_path), recursive=False); observer.start()

    # tray menu callbacks
    def open_inbox():  webbrowser.open(watch_path.as_uri())
    def open_backup(): webbrowser.open(Path(cfg["backup_folder"]).as_uri())
    def open_log():    webbrowser.open(log_path.as_uri())
    def toggle_pause(icon, item):
        paused = sender.toggle_pause()
        icon.title = f"FolderMonitorAdrian ({'Paused' if paused else 'Running'})"
    def on_exit(icon, item):
        icon.visible = False
        observer.stop(); observer.join(timeout=3)
        sender.stop()
        icon.stop()

    icon_img = load_icon_image(base)
    from pystray import Menu, MenuItem
    menu = Menu(
        MenuItem("Open Inbox", lambda icon, item: open_inbox()),
        MenuItem("Open Backup", lambda icon, item: open_backup()),
        MenuItem("Open Log", lambda icon, item: open_log()),
        MenuItem(lambda item: "Resume" if sender.paused else "Pause", toggle_pause),
        MenuItem("Exit", on_exit)
    )
    icon = pystray.Icon("FolderMonitorAdrian", icon_img, "FolderMonitorAdrian (Running)", menu)
    try:
        icon.run()  # blocks; handles clean shutdown via menu Exit
    finally:
        try:
            observer.stop(); observer.join(timeout=3)
        except Exception:
            pass
        sender.stop()
        logging.info("FolderMonitorAdrian stopped.")

if __name__ == "__main__":
    main()
