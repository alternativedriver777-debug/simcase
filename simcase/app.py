from .api import API
from .ui import HTML


def main():
    import webview

    api = API()
    webview.create_window(
        "Симулятор кейсов",
        html=HTML,
        js_api=api,
        width=1460,
        height=920,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
