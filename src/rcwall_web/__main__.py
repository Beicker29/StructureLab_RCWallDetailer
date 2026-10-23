"""Run the local prototype, bound exclusively to loopback."""

import uvicorn


def main():
    uvicorn.run("rcwall_web.app:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
