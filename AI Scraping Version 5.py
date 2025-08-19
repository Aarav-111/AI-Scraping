import sys, os, json, urllib.parse
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer

SYSTEM_PROMPT = "Your name is Core-AI, trained by Prolabs Robotics."
HISTORY_FILE = "convo.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        data = json.load(open(HISTORY_FILE))
        # normalize any old format
        normalized = []
        for h in data:
            if "role" in h and "content" in h:
                normalized.append(h)
            elif "user" in h:
                normalized.append({"role": "user", "content": h["user"]})
            elif "ai" in h:
                normalized.append({"role": "assistant", "content": h["ai"]})
        return normalized
    return []

def save_history(history):
    json.dump(history, open(HISTORY_FILE, "w"), indent=2)

app = QApplication(sys.argv)
browser = QWebEngineView()

user_prompt = input("User prompt: ")

history = load_history()
combined = SYSTEM_PROMPT + "\n" + "\n".join(
    f"{h['role']}: {h['content']}" for h in history[-20:]
) + f"\nUser: {user_prompt}"
encoded = urllib.parse.quote(combined, safe="")
URL = f"https://chatgpt.com/?q={encoded}"

browser.setUrl(QUrl(URL))

# Run browser in background
browser.resize(1, 1)
browser.showMinimized()

def auto_accept():
    js = """
    let acceptBtn = [...document.querySelectorAll("button")].find(b => 
        b.innerText.toLowerCase().includes("accept")
    );
    if (acceptBtn) acceptBtn.click();

    let closeBtn = document.querySelector('[aria-label="Close"]');
    if (closeBtn) closeBtn.click();
    """
    browser.page().runJavaScript(js)

def scrape_response():
    js = """
    var msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
    msgs.length ? msgs[msgs.length-1].innerText : "";
    """
    browser.page().runJavaScript(js, lambda res: handle_response(res))

def handle_response(text):
    if text:
        print("\n--- ChatGPT Answer ---\n")
        print(text.strip())
        history.append({"role": "user", "content": user_prompt})
        history.append({"role": "assistant", "content": text.strip()})
        save_history(history)
        QTimer.singleShot(1000, app.quit)

QTimer.singleShot(3000, auto_accept)

timer = QTimer()
timer.timeout.connect(scrape_response)
timer.start(2000)

sys.exit(app.exec())
