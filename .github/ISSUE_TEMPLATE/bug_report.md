---
name: Bug report
about: File a bug report for smbus3
title: ''
labels: bug
assignees: eindiran

---

**Describe the bug**
A clear and concise description of what the bug is, what OS you are on, what hardware you are using, etc. Please include what you expected to happen and a description of what actually happened, logs, errors thown, etc.

**To Reproduce**
Minimal Python 3 code required to reproduce the issue.

**Debugging information**
Fill in the following information. Replace `<bus number>` with the expected bus number of the i2c device.

1. Output of `uname -a`:
2. Output of `i2cdetect -y <bus number>`:
3. Output of `i2cdetect -F <bus number>`:
4. Output of `python3 --version`:
5. Output of `python3 -c 'import smbus3; print(smbus3.__version__)'`

**Additional context**
Add any other context about the problem here.
