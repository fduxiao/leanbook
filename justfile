test:
    uv run -m unittest tests

check:
    uv tool run ruff check ./src

todo:
    uv tool run ruff check --select=FIX ./src

format:
    uv tool run ruff format
