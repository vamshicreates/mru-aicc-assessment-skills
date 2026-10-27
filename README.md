# MRU AICC Assessment Skills

Three Codex skills for Malla Reddy University's AI in Content Creation & Creator Economy assessment framework. Each assessment is independently scored out of 100.

| Skill | Assessment |
| --- | --- |
| `mru-aicc-assessment-1-theory` | Week 3 theory questionnaire; requires the actual Google Form answer key and question mark settings |
| `mru-aicc-assessment-2-ai-advert` | Week 6 AI brand advertisement; seven official criteria |
| `mru-aicc-assessment-3-self-avatar` | Week 9 self-avatar introduction; seven official criteria |

The workflow reviews submissions, records evidence and deductions, creates an individual feedback PDF and student detail tab, and writes a separate Google Sheets results workbook. Each Results row includes the student's name, number, score, submission link, and individual assessment PDF link. Video feedback uses timestamps. Inaccessible or incomplete reviews remain pending.

## Install with a prompt

Open [the installation prompt](INSTALL_PROMPT.md), copy it into Codex, and let Codex install the skills for your operating system.

## Install manually

Requirements: Codex, Python 3.10 or newer, and network access to install the PDF dependency. Git is optional: the GitHub **Code → Download ZIP** option also works. Extract the ZIP first and open a terminal in the extracted repository folder.

Windows PowerShell:

```powershell
git clone https://github.com/vamshicreates/mru-aicc-assessment-skills.git
cd mru-aicc-assessment-skills
py -3 install.py --with-runtime
```

If the Python launcher is unavailable but `python` is installed, use `python install.py --with-runtime`.

macOS / Linux:

```sh
git clone https://github.com/vamshicreates/mru-aicc-assessment-skills.git
cd mru-aicc-assessment-skills
python3 install.py --with-runtime
```

The installer uses `$CODEX_HOME/skills` when `CODEX_HOME` is configured, otherwise the current user's `~/.codex/skills`. On Windows the default is `%USERPROFILE%\.codex\skills`. It installs only these three skill folders. `--with-runtime` creates an isolated shared Python environment under the Codex home directory's `skill-runtimes/mru-aicc-assessments` folder and installs ReportLab there. Existing identical skills are left current; differing skills require `--force`, which preserves a backup before replacing them. No administrator privileges or shell execution-policy changes are required for the Python installer.

Open a new Codex chat or restart Codex to refresh skill discovery.

Optional flags:

```text
--skill mru-aicc-assessment-2-ai-advert   Install one selected skill
--target "path/to/skills"               Choose a skill directory
--force                               Back up and update differing installed skills
--with-runtime                        Install the isolated report dependency
--runtime-dir "path/to/runtime"         Choose the isolated runtime directory
```

Omit `--with-runtime` if Codex already has a Python runtime with ReportLab. Each installed skill includes its own `requirements.txt` and [platform setup instructions](mru-aicc-assessment-2-ai-advert/references/platform-setup.md).

## Start an assessment

Connect Google Drive/Sheets in Codex, then invoke a skill with your actual response sheet:

```text
Use $mru-aicc-assessment-2-ai-advert to assess every student in [GOOGLE SHEET LINK]. Review the submitted videos and create a new results workbook with each student's detailed assessment and individual PDF link in their row.
```

For theory, provide the actual questionnaire, correct answers, and question-level mark allocation; these are not supplied in the framework PDF. For video assignments, Codex needs access to the submitted files and tools capable of reviewing their complete picture and audio. The included Python helper renders evidence and marks supplied by the assessor; it does not automatically watch videos or determine grades. Optional FFmpeg/FFprobe supports media inspection but does not replace actual audio/visual review.

## Run a report helper

Prepare the JSON described in the selected skill's `references/report-input.md`. Use the shared runtime reported by the installer, or another Python with ReportLab:

```text
<report-python> <installed-skill>/scripts/build_report.py student.json --output-dir reports
```

Paths with spaces must be quoted. JSON is read as UTF-8, including files with a UTF-8 BOM produced by some Windows editors. CSV is written as UTF-8 with BOM for spreadsheet interoperability. Upload the PDF and write Google Sheets values as instructed by the skill; a local report is not an uploaded assessment.

## Checks

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

GitHub Actions runs installation, update/backup, rubric, report validation, UTF-8 input, and PDF/CSV checks on Windows, macOS, and Linux. These are packaging and helper checks; they do not validate a live Google connection or a student's grade.

## Rubric source

The supplied **MRU AICC Final Assessment Framework and Rubrics 2026.pdf** is bundled in each skill's `references/framework.pdf`; its SHA-256 and relevant page are recorded in `rubric.json`. This package implements the supplied framework. The institution's original document remains attributed to its author. No student responses, reports, account credentials, or questionnaire answer keys are included.
