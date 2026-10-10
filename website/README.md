# Online editions

The site is generated from `book/`, including `book/en/`. Source text is not edited by the generator. Generated files are excluded from Git.

```sh
python -m pip install -r website/requirements.txt
python website/build.py --base-path /ai-fde-business-playbook/
python website/check.py
python -m http.server 8000 --directory _site
```

For a local preview at the server root, build with `--base-path /`. The deployed site uses the repository prefix. GitHub Actions builds and deploys `_site` only, after source and local-link checks pass. Original figures are copied without re-encoding; the eight marked English figures always use PNG. Other English figures use SVG, and Chinese figures use their published PNGs.

Every chapter, worksheet, reading guide, author page and sharing notice has its own URL. The language switch retains the chapter or worksheet number. Heading anchors are stable for unchanged source headings. Search indexes are downloaded only when opening search; queries and reading progress stay in the reader's browser. No analytics or third-party assets are requested.
