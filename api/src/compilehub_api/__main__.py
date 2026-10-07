import uvicorn


def main() -> None:
    uvicorn.run("compilehub_api.main:app", host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
