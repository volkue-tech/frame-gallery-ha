# Changelog

## 0.1.0.dev0 (development build, not released)

- First packaging of the app for Home Assistant OS (`aarch64` and `amd64`).
- Sources: the Art Institute of Chicago (period filter), the Cleveland Museum of Art (department and period filters), and your own images.
- One bounded run per start: at most two minutes, and at most 70 seconds when nothing matches.
- No work is sent twice while unsent works remain; an upload whose outcome is unknown is held back for 30 days.
- Workers that decode images or talk to the TV run as an unprivileged user with memory, CPU, and file limits.
- Not yet tested against a real TV or on a Home Assistant Green.
