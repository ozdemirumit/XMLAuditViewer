# XML Audit Viewer

**A fast, dependency-free desktop viewer and live-tail tool for CIFS/SMB security audit logs in XML format — NetApp ONTAP and Huawei OceanStor.**

Open multi-hundred-MB audit files in seconds, follow them like `tail -f` while the storage array writes new events, filter by user / IP / time / event type, drill into suspicious activity with one right-click, and export the result to CSV for your SOC or auditors — all without Splunk, ELK or any external dependency.

[![PyPI](https://img.shields.io/pypi/v/xml-audit-viewer.svg?label=pypi&cacheSeconds=300)](https://pypi.org/project/xml-audit-viewer/) [![Python versions](https://img.shields.io/pypi/pyversions/xml-audit-viewer.svg?label=python&cacheSeconds=300)](https://pypi.org/project/xml-audit-viewer/) ![status: working](https://img.shields.io/badge/status-working-brightgreen) ![deps: stdlib only](https://img.shields.io/badge/deps-stdlib%20only-success) ![platforms](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue) ![license: MIT](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Table of contents

- [What it is for](#what-it-is-for)
- [Supported storage systems](#supported-storage-systems)
- [Features](#features)
- [Install](#install)
- [Quick start](#quick-start)
- [User guide](#user-guide)
- [Supported events](#supported-events)
- [How fields are mapped](#how-fields-are-mapped)
- [Log format examples](#log-format-examples)
- [Real-world example](#real-world-example)
- [Build a Windows `.exe`](#build-a-windows-exe)
- [How it works (technical notes)](#how-it-works-technical-notes)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license) · [Contributing](#contributing)

---

## What it is for

Storage arrays can write a Windows-style security audit trail for every CIFS/SMB share: who logged on, from which IP, which file or folder they opened, read, changed or deleted, and which logons failed. That data lands in large XML files that are painful to read in a text editor.

XML Audit Viewer turns those files into a sortable, filterable, colour-coded table so you can answer questions such as:

- Who accessed this file or share, and when?
- Which IP is hammering the array with failed logons (password spraying, credential stuffing)?
- Did anyone change permissions or auditing settings?
- What is service account *X* doing on share *Y* right now? (live tail)

It is a single Python file using only the standard library (`tkinter`), so it can run on a locked-down admin workstation, or be shipped as a single `.exe`.

---

## Supported storage systems

| Vendor | Product / log source | Format details |
|---|---|---|
| **NetApp** | ONTAP CIFS security audit logs (`audit_*.xml`, rotated `.xml-1`, `.xml.0` …) | One `<Event>` per line, Windows event-style schema. |
| **Huawei** | OceanStor CIFS audit logs (e.g. OceanStor 5510) | `<Events>` wrapper, namespaced `<Event xmlns='http://schemas.huawei.com/events/audit-event'>`, provider `Huawei-Security-Auditing`, `Computer` = `<array>/<vStore>`. |

The vendor is **detected automatically** from the file (see [Vendor selector](#top-bar)). Both vendors use the same Windows audit event IDs and field names, so they share one parser and one table.

---

## Features

**Loading and following**
- **Open File** — load a file once, instantly, with no following.
- **Start Tail / Stop Tail** — follow the file like `tail -f`; new events stream into the table. If you opened the file first, tailing continues exactly where the load ended (no duplicates, no re-reading).
- **Folder (rotated)…** — load a whole folder of audit files (`audit.xml`, `audit.xml-1`, `audit.xml.0` …) in chronological order, then tail the newest one.
- **Rotation-aware tail** — detects rename-based rotation, deletion + recreation and in-place truncation, and re-reads the new file automatically.
- **Partial-event safe** — an event that is only half written when the file is read is held back until its closing tag arrives.

**Understanding the data**
- **Unified columns** — logon events and file-operation events share one `User` / `IP` / `Share` / `Object` / `Action` view; you do not need to know which schema applies.
- **Share / path split** — `(ShareName);/dir/file.pdf` is split into a `Share` column and a path.
- **Readable access rights** — Windows message codes like `%%4416 %%4423` are decoded to *ReadData/ListDirectory; ReadAttributes*.
- **Colour coding** — green rows = *Audit Success*, red rows = *Audit Failure*.
- **Detail pane** — select a row to see every field of the event, including fields the viewer does not know about.

**Analysis**
- **Filters** — Event ID, Result, user, IP, time range (with *Last 1 hour* / *Last 24 hours* shortcuts) and free-text search across **all** fields, applied as you type.
- **Right-click drill-in** — filter by this IP / user / Event ID / domain / failure reason, or run "this IP + this user, failures only" in one click.
- **Statistics window** — 11 tabs of top-N breakdowns, including failure hot-spots and file-access summaries; double-click a row to filter the main table.
- **CSV export** — exports exactly what the filters show; UTF-8 with BOM and `;` delimiter so Excel opens it correctly, including Turkish characters.

**Robustness**
- **Malformed-event repair** — bare `&` in file names, control characters and non-UTF-8 bytes (legacy code pages such as cp1254) are repaired instead of being dropped.
- **Nothing is lost silently** — events that still cannot be parsed are counted and shown in the status bar.
- **Unknown fields are kept** — new or vendor-specific fields appear in the detail pane and are searchable.

**Deployment**
- **Zero dependencies** — Python standard library only.
- **Single-file `.exe`** — `build.bat` produces one self-contained `XMLAuditViewer.exe` with no external DLLs.
- **Cross-platform** — Windows, Linux, macOS; Python 3.10 – 3.14.

---

## Install

### From PyPI

```bash
pip install xml-audit-viewer
xml-audit-viewer
```

### From source

```bash
git clone https://github.com/ozdemirumit/XMLAuditViewer.git
cd XMLAuditViewer
python xml_audit_viewer.py
```

### As a Windows executable

Download the ready-made single-file `XMLAuditViewer.exe` from the [Releases page](https://github.com/ozdemirumit/XMLAuditViewer/releases) — no Python needed. Or build it yourself with `build.bat` (see [Build a Windows `.exe`](#build-a-windows-exe)) and copy the single `XMLAuditViewer.exe` to any Windows machine — no Python needed there.

> **Linux note:** `tkinter` is a separate package on many distributions, e.g. `sudo apt install python3-tk` (Debian/Ubuntu) or `sudo dnf install python3-tkinter` (Fedora).

---

## Quick start

> **Try it without your own logs:** the repo ships two synthetic sample files with fake users and documentation-range IPs — [`examples/sample_netapp_audit.xml`](examples/sample_netapp_audit.xml) and [`examples/sample_huawei_audit.xml`](examples/sample_huawei_audit.xml). The NetApp one contains a password-spraying pattern (60 failed logons from `203.0.113.77`) to find with the *Statistics* window.

```bash
xml-audit-viewer                                       # start empty, pick a file in the GUI
xml-audit-viewer /path/to/audit.xml                    # pre-fill the file path
xml-audit-viewer /path/to/audit.xml --tail             # load and follow immediately
xml-audit-viewer audit.xml --filter-ip 10.0.0.5 --only-failures --tail
xml-audit-viewer huawei_audit.xml --vendor huawei --tail
```

(From source, substitute `python xml_audit_viewer.py` for `xml-audit-viewer`.)

### Command-line options

| Flag | Description |
|---|---|
| `path` (positional) | XML file to use on startup. On its own it only fills in the file box; add `--tail` to load it. |
| `--tail`, `-t` | Load the file and start following it immediately. |
| `--filter-ip IP` | Pre-fill the *IP contains* filter. |
| `--filter-user USER` | Pre-fill the *User contains* filter. |
| `--filter-eventid ID` | Pre-select an Event ID, e.g. `4625`. |
| `--vendor V` | Vendor label: `auto` (default), `netapp` or `huawei`. |
| `--only-failures` | Show only *Audit Failure* events. |

---

## User guide

### Top bar

| Control | What it does |
|---|---|
| **File** box + **Browse…** | Choose the audit XML file. |
| **Open File** | Load the whole file once. Stops any running tail. |
| **Start Tail / Stop Tail** | Follow the file for new events. If the file was opened with *Open File*, continues from where it ended; otherwise reads the file from the start and then follows it. |
| **Folder (rotated)…** | Pick a folder; loads every `*.xml`, `*.xml-N`, `*.xml.N` file oldest → newest, then tails the newest. |
| **Vendor** | `Auto` (default) uses the vendor detected from each event and shows it in the status bar; `NetApp` / `Huawei` force the label. Parsing is identical for both — this only sets the label shown in the status bar, detail pane, CSV and search. |
| **Reload** | Re-read the file from scratch; tailing stays on if it was on. |
| **Statistics…** | Open the statistics window for the currently filtered events. |
| **Export CSV…** | Save the currently filtered events as CSV. |

### Filters

| Filter | Behaviour |
|---|---|
| **Event ID** | Drop-down filled automatically with the IDs found in the data. |
| **Result** | `All`, `Audit Success`, `Audit Failure`. |
| **User contains** | Case-insensitive substring of the unified `User`. |
| **IP contains** | Case-insensitive substring of the unified `IP`. |
| **From / To** | `YYYY-MM-DD HH:MM[:SS]`, compared against the displayed time. *Last 1 hour* / *Last 24 hours* set the range relative to the **newest event in the data** (so it works for old logs too). |
| **Search (all fields)** | Case-insensitive search across every parsed field, including unknown extra fields. |
| **Apply / Reset** | Apply immediately / clear all filters. |
| **Auto-scroll** | Keep the newest row in view while tailing. |
| **Filter as you type** | Re-filter 250 ms after you stop typing. Turn off for very large datasets and press Enter / Apply instead. |

### The event table

Columns: **Time**, **ID**, **Event**, **Result**, **IP**, **User**, **Domain**, **Share**, **Object**, **Action / Reason**. Click a header to sort (click again to reverse). Rows are green for success and red for failure.

The **Action / Reason** column shows, depending on the event: the requested access (*Read Data…*, *Write Data…*), *Object deleted*, *Handle closed*, *Permissions changed*, *Audit settings changed*, the **failure reason** of a failed logon, or *LogonType N* for a successful logon.

The table shows the most recent **10,000** matching rows; everything stays in memory and in the filters/statistics/CSV (see [Limitations](#limitations)).

### Detail pane

Select a row to see all of its fields (time, vendor, IDs, user/IP, share/path, decoded access rights, raw access mask, SIDs, handle ID, and any extra fields such as Huawei's `SubjectUnix`).

### Right-click menu

Right-click a row to:
- filter by that **IP**, **user**, **Event ID**, **domain**, or **failure reason**;
- run **"This IP + this user (failure analysis)"**, **"Only failures from this IP"** or **"Only failures from this user"**;
- copy the **IP**, the **user**, or the **full event details** to the clipboard;
- **reset all filters**.

### Statistics window

Computed over the currently filtered events. The header shows totals, success/failure counts, unique IPs and users, time range and per-vendor counts.

| Tab | Shows |
|---|---|
| Event types | Count and share per Event ID / name. |
| Failure IPs | Top IPs by failed events — double-click to filter the main table. |
| Failure users | Top users by failed events — double-click to filter. |
| All IPs | Top IPs by total events. |
| Domains | Events per domain. |
| Failure reasons | Why logons failed (e.g. *No such user account*). |
| Shares | Events per share. |
| Top objects | Most-accessed files/folders. |
| File access users | Users generating the most file-operation events — double-click to filter. |
| Access types | What was done to objects (read, write, delete, permission change …). |
| Hourly distribution | Events per hour as a text bar chart. |

### CSV export

Exports the **filtered** events with these columns (`;`-delimited, UTF-8 with BOM):

`TimeDisplay, Vendor, EventID, EventName, Source, Result, Computer, IP, User, Domain, Share, ObjectName, ObjectType, Action, AccessMask, IpAddress, IpPort, TargetUserName, TargetDomainName, TargetUserSid, Status, FailureReason, FailureReasonString, AuthenticationPackageName, LogonType`

---

## Supported events

| Event ID | Name | Family | Typical key fields | Action column |
|---|---|---|---|---|
| 4624 | Logon Attempt / Success | Logon | `TargetUserName`, `IpAddress`, `LogonType`, `AuthenticationPackageName` | `LogonType N` |
| 4625 | Logon Failure | Logon | `TargetUserName`, `IpAddress`, `FailureReasonString` | failure reason |
| 4634 | Logoff | Logon | `TargetUserName`, `IpAddress` | – |
| 4656 | Open Object | File operation | `SubjectUserName`, `SubjectIP`, `ObjectName`, `DesiredAccess`, `AccessList` | requested access |
| 4658 | Close Handle | File operation | `SubjectUserName`, `HandleID` | *Handle closed* |
| 4660 | Delete Object | File operation | `SubjectUserName`, `ObjectName` | *Object deleted* |
| 4663 | Get Object Attributes / Access | File operation | `SubjectUserName`, `ObjectName`, `InformationRequested` | requested access |
| 4670 | Permissions Changed | File operation | `ObjectName`, `OldSD`, `NewSD` | *Permissions changed* |
| 4907 | Auditing Settings Changed | File operation | `ObjectName`, `OldSD`, `NewSD` | *Audit settings changed* |

**Any other Event ID is still parsed and shown.** It appears in the table, in the Event ID filter and in the statistics; user, IP and object columns are filled from the usual field names, only the *Action* summary stays empty. All fields are available in the detail pane and in the search. If your array emits additional IDs, open an issue with a sample line.

### Decoded access rights

`AccessList` values (`%%NNNN`) are translated for the *Action* column and the detail pane:

| Code | Meaning | Code | Meaning |
|---|---|---|---|
| `%%1537` | DELETE | `%%4419` | ReadEA |
| `%%1538` | READ_CONTROL | `%%4420` | WriteEA |
| `%%1539` | WRITE_DAC | `%%4421` | Execute/Traverse |
| `%%1540` | WRITE_OWNER | `%%4422` | DeleteChild |
| `%%1541` | SYNCHRONIZE | `%%4423` | ReadAttributes |
| `%%4416` | ReadData/ListDirectory | `%%4424` | WriteAttributes |
| `%%4417` | WriteData/AddFile | `%%4418` | AppendData/AddSubdirectory |

Unknown codes are shown as-is.

---

## How fields are mapped

Logon events use `Target*` / `IpAddress`, file-operation events use `Subject*` / `SubjectIP`. The viewer merges them into unified columns:

| Unified column | Taken from (first non-empty) |
|---|---|
| **User** | `SubjectUserName`, then `TargetUserName` |
| **Domain** | `SubjectDomainName`, then `TargetDomainName` |
| **IP** | `SubjectIP`, then `IpAddress` |
| **Share** / **Path** | `ObjectName` of the form `(Share);/path` |
| **Action** | depends on Event ID, see [Supported events](#supported-events) |
| **Time** | `TimeCreated/@SystemTime`, shown as `YYYY-MM-DD HH:MM:SS` |

---

## Log format examples

### Huawei OceanStor

```xml
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<Events>
<Event xmlns='http://schemas.huawei.com/events/audit-event'><System><Provider Name='Huawei-Security-Auditing' .../><EventID>4656</EventID><EventName>Open Object</EventName><Source>CIFS</Source><Result>Audit Success</Result><TimeCreated SystemTime='2026-09-30T20:59:53.408261000Z'/><Computer>ARRAY01/NAS_CIFS_vStore</Computer>...</System><EventData>
  <Data Name='SubjectIP' IPVersion='4'>10.30.1.153</Data>
  <Data Name='SubjectUserName'>suboa</Data>
  <Data Name='SubjectDomainName'>EXAMPLE</Data>
  <Data Name='ObjectType'>File</Data>
  <Data Name='ObjectName'>(Files02);/Reports/2026/09/26/report.pdf</Data>
  <Data Name='AccessList'>%%4416 %%4419 %%4423 %%1538 %%1541 </Data>
  <Data Name='DesiredAccess'>Read Data (or List Directory);Read Attributes;</Data>
</EventData></Event>
</Events>
```

### NetApp ONTAP

```xml
<Event><System><EventID>4625</EventID><EventName>Logon Failure</EventName><Result>Audit Failure</Result>
<TimeCreated SystemTime='2026-04-03T13:15:25.954874000Z'/>...</System><EventData>
  <Data Name='IpAddress'>172.17.10.165</Data>
  <Data Name='TargetUserName'>tb2783</Data>
  <Data Name='FailureReasonString'>No such user account</Data>
</EventData></Event>
```

Events may be on a single line or span several lines; they are located by their `<Event …> … </Event>` tags.

---

## Real-world example

Quick triage of a 54 MB / 54,806-event NetApp audit file from a production CIFS share:

```
Event distribution
  4625 Logon Failure          49,839
  4624 Logon Attempt           3,003
  4634 Logoff                  1,841
  4656 Open Object                54
  4663 Get Object Attributes      52
  4907 Auditing Settings           9
  4670 Permissions Changed         8

Top failure IPs
  172.17.10.165   37,350  (74.9%)   <- single host, almost the whole file
  172.17.10.150    3,625   (7.3%)
  172.17.9.9       2,047   (4.1%)

Top failure usernames
  tb2783          37,350  (74.9%)   <- repeating against the same SVM
  tb1386           3,675   (7.4%)

Top failure reasons
  No such user account                              44,186  (88.7%)
  User name is correct but the password is wrong    3,858   (7.7%)
  Unknown user name or bad password                 1,780   (3.6%)
```

A single host hammering one username with *No such user account* over multiple days is a classic credential-stuffing / stale-credential pattern. In the GUI it takes two clicks: **Statistics…** → double-click `172.17.10.165` in *Failure IPs* → the main table is filtered to that host, ready for review or **Export CSV…**.

Another typical workflow — *"who touched this folder?"*: type the folder name in **Search**, set *Event ID* to `4656`, then open **Statistics… → File access users**.

---

## Build a Windows `.exe`

Ship the viewer to colleagues who don't have Python installed. The build produces a **single, self-contained `XMLAuditViewer.exe`** — the Python runtime, Tcl/Tk and every required DLL are packed inside it, so **no external DLLs, no Python install and no extra files** are needed on the target machine. Copy the one file anywhere and run it.

### Using `build.bat` (recommended)

On a Windows machine with Python 3.10+ installed:

1. Open the repo folder.
2. Double-click `build.bat` (or run it from `cmd`).
3. Take the result from `dist\XMLAuditViewer.exe`.

What the script does:

- Removes previous `build\` and `dist\` folders.
- Installs [PyInstaller](https://pyinstaller.org) with `pip` if it is missing.
- Runs PyInstaller with `--onefile --windowed --clean`: one exe, no console window.
- Stops with an error message if the build fails.

### Manual build

```cmd
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "XMLAuditViewer" --clean xml_audit_viewer.py
```

**Notes**

- A `--onefile` exe unpacks itself to a temporary folder on every start, so launch takes a second or two longer. Corporate antivirus sometimes flags PyInstaller's onefile bootloader — whitelist the exe if that happens. If it keeps being quarantined, build without `--onefile` (folder build in `dist\XMLAuditViewer\`, more AV-friendly, but you must ship the whole folder).
- The exe must be built on Windows; PyInstaller cannot cross-compile from Linux/macOS.
- Add `--icon=audit.ico` for a custom icon.
- Lightweight alternative when target machines already have Python: `python -m zipapp . -m "xml_audit_viewer:main" -o XMLAuditViewer.pyz` produces a ~40 KB single-file zipapp.

---

## How it works (technical notes)

- **Parsing** — events are located with a regular expression on `<Event …> … </Event>` and parsed individually with `xml.etree.ElementTree`. XML namespaces are stripped so NetApp and Huawei events go through the same code. If strict parsing fails, a lenient retry fixes bare `&`, control characters and non-UTF-8 encodings (UTF-8 → cp1254 → latin-1); anything still unreadable is counted in the status bar.
- **Vendor detection** — an event is labelled *Huawei* when its namespace or `Provider/@Name` contains "huawei", otherwise *NetApp*.
- **Tail** — a background thread polls once per second, reads from the last position, keeps unparsed trailing bytes in a buffer (so half-written events never reach the table) and hands parsed events to the GUI thread through a `queue.Queue`. Rotation is detected by inode/device change, file shrinkage, a file that disappears and reappears, and a changed first 4 KB of the file (in-place rewrite).
- **GUI** — never blocks on disk I/O. Filtering is debounced (250 ms), and the table is capped at the newest 10,000 matching rows for rendering speed.

---

## Limitations

- The table shows at most **10,000** rows (change `MAX_DISPLAY_ROWS` at the top of the file). All events stay in memory; the cap only affects rendering. Statistics and CSV cover **all** filtered events, not just the visible ones.
- Memory use is roughly **1.5 KB per event** — 1 M events ≈ 1.5 GB RAM. For larger datasets filter first or split the file.
- Times are shown exactly as stored in `TimeCreated/@SystemTime` (UTC); there is **no time-zone conversion**.
- Huawei and NetApp share one parser. Vendor-specific fields that the viewer does not know are shown in the detail pane and searchable, but have no dedicated column.
- Only the XML audit format is supported (not EVTX, syslog or JSON).

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ModuleNotFoundError: No module named 'tkinter'` | Install the Tk package for your Python (`python3-tk` on Debian/Ubuntu). On Windows reinstall Python with *tcl/tk* enabled. |
| Table stays empty | Check the file really contains `<Event …>` blocks. Look at the status bar for the *Unparsable / repaired* counters. |
| Status bar shows *Unparsable: N* | N events are not valid XML even after repair. Send a sample line in an issue. |
| Wrong vendor label | Switch **Vendor** from *Auto* to the right vendor. |
| New events don't appear | Click **Start Tail** (Open File does not follow). Check *Filter as you type* / active filters and *Auto-scroll*. |
| Time filter returns nothing | Use `YYYY-MM-DD HH:MM` and remember times are UTC as stored in the log. |
| Antivirus blocks the exe | See the notes in [Build a Windows `.exe`](#build-a-windows-exe). |

---

## Development

```bash
git clone https://github.com/ozdemirumit/XMLAuditViewer.git
cd XMLAuditViewer
python xml_audit_viewer.py            # run
python test_tail_basic.py             # tail reader scenarios (standalone script)
python test_tail_hard.py              # stress / rotation scenarios (standalone script)
python -m pytest test_huawei.py       # parser tests (needs: pip install pytest)
```

Everything lives in `xml_audit_viewer.py`: the parser (`parse_event`), the tail thread (`TailReader`) and the GUI (`AuditViewer`). Version history is in [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome — especially:

- Sample lines for event IDs or fields not yet covered (other NetApp / Huawei releases, NFS audit, anti-virus events …)
- Other vendors that emit Windows-style XML audit events
- Performance improvements for very large files (memory-mapped reading)
- Optional Splunk / ELK forwarder mode
