---
name: Bug report or support request
about: Use this template if you're having trouble with your SPIRO
title: ''
labels: ''
assignees: ''

---

**Describe the problem**
A clear and concise description of what the problem is.

**Log output**
For many problems, log output helps us figure out what the issue is. To obtain good log output, first reproduce the problem on your SPIRO. Then, log in via SSH and enter the following command: `journalctl --user-unit=spiro -n 200 --no-pager` and paste it into this issue. Thanks!
