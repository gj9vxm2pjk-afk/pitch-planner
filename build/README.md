# Build files for the Weekend Pitch Planner

`refresh.py` rebuilds the page from the club's fixtures sheet.

1. Save the base64 text of each sheet's first tab (Drive `download_file_content`, `text/csv`): fixtures to `latest.b64`, paddock & scrum machine bookings to `bookings.b64`, weekly training to `training.b64`.
2. Run `python3 refresh.py`. It validates the data and writes `index.html`.
3. Copy `build/index.html` to the repo root as `index.html` and commit it. Cloudflare and GitHub Pages publish from the root.

`latest.b64`, `latest.csv`, `index.html` and `artifact.html` in this folder are git-ignored.
