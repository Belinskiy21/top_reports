from watchfiles import run_process


def main() -> None:
    _ = run_process(
        ".",
        target="scripts/check.sh",
        watch_filter=None,
        debounce=800,
        step=100,
    )


if __name__ == "__main__":
    main()
