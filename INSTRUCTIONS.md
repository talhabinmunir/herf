# Setup instructions

Herf is a Windows desktop app (pywebview + Microsoft Edge WebView2). These steps cover running it from source and building a standalone .exe.

## Run from source

1. Install Python 3.10 or newer from [python.org](https://www.python.org/) — tick "Add to PATH" during install.
2. Open Command Prompt in this folder and run:

```
pip install -r requirements.txt
python main.py
```

pywebview uses Microsoft Edge WebView2, which is already present on Windows 10/11.

## Build a standalone .exe

```
pip install pyinstaller
pyinstaller --noconsole --onefile --icon herf_icon.ico --add-data "herf/ui;herf/ui" --add-data "herf/data;herf/data" --name Herf main.py
```

The .exe appears in the `dist` folder. Both `--add-data` flags are required: `herf/ui` holds the UI (`index.html`), and `herf/data` holds the bundled Quran text used by the Check Quran verses feature. Leaving either out produces an exe that is missing that piece at runtime.

`build/` and `dist/` (and the generated `Herf.spec`) are not tracked in this repo — each machine should build its own.

## Troubleshooting

- **"pywebview uses Microsoft Edge WebView2"** — if the app window fails to open, install the [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (it ships with Windows 10/11 by default, but some stripped-down installs lack it).
- **python-docx is not installed** — shown if you try to export .docx without the dependency; run `pip install python-docx` or reinstall via `pip install -r requirements.txt`.
- **Antivirus flags the built .exe** — this is common for unsigned PyInstaller one-file executables and is a false positive; running from source avoids it entirely.
