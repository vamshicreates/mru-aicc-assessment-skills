# Installation prompt

Copy this prompt into Codex on Windows, macOS, or Linux:

```text
Install all three MRU AICC assessment skills from https://github.com/vamshicreates/mru-aicc-assessment-skills on this computer.

Clone the repository into a suitable local folder, or download and extract its GitHub ZIP if Git is unavailable. Read its README.md and install.py. Detect this computer's operating system and an available Python 3.10+ interpreter; on Windows check py -3 and python, and on macOS/Linux check python3 and python.

Run install.py --with-runtime using that interpreter. Respect CODEX_HOME when set; otherwise install in the current user's .codex/skills folder. Do not use another person's absolute paths. If existing skill files differ, back them up and update only these three skills with the installer's --force option. Do not change unrelated skills or Codex settings. Verify all three installed SKILL.md files and that the isolated report runtime imports ReportLab. If an install/network permission or missing Python prevents completion, identify the exact remaining step without claiming installation succeeded.

Tell me the installed skill names, where they are installed, and how to start a new assessment. Explain that I must connect Google Drive/Sheets, provide the assignment response sheet, and provide the actual Form answer key and question marks for Assessment 1. Do not access or grade student submissions during installation. Remind me to open a new Codex chat or restart Codex if the skills do not appear immediately.
```
