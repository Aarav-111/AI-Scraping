import sys, urllib.parse
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PySide6.QtCore import QUrl, QTimer

SYSTEM_PROMPT = "Your name is Core-AI, trained by Prolabs Robotics."

class SilentPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        return

app = QApplication(sys.argv)
browser = QWebEngineView()
browser.setPage(SilentPage(browser))

suppress = QWebEngineScript()
suppress.setName("suppress-console-warn-error")
suppress.setInjectionPoint(QWebEngineScript.DocumentCreation)
suppress.setRunsOnSubFrames(True)
suppress.setWorldId(QWebEngineScript.MainWorld)
suppress.setSourceCode("console.warn=function(){};console.error=function(){};")
browser.page().scripts().insert(suppress)

history = []

state = {"mode": "idle", "current_user": "", "last_saved_assistant": "", "last_scraped": "", "stable": 0, "scraping_enabled": False}

def build_and_nav(prompt):
    history.append({"role": "user", "content": prompt})
    combined = SYSTEM_PROMPT + "\n" + "\n".join(f"{h['role']}: {h['content']}" for h in history[-20:]) + f"\nUser: {prompt}"
    encoded = urllib.parse.quote(combined, safe="")
    url = f"https://chatgpt.com/?q={encoded}"
    state["current_user"] = prompt
    state["last_scraped"] = ""
    state["stable"] = 0
    state["scraping_enabled"] = False
    state["mode"] = "waiting"
    browser.setUrl(QUrl(url))

def ask_next():
    try:
        prompt = input("User prompt: ")
    except EOFError:
        prompt = ""
    if not prompt.strip():
        ask_next()
        return
    build_and_nav(prompt)

def auto_accept():
    js = """
    let acceptBtn = [...document.querySelectorAll("button")].find(b => b.innerText && b.innerText.toLowerCase().includes("accept"));
    if (acceptBtn) acceptBtn.click();
    let closeBtn = document.querySelector('[aria-label="Close"]');
    if (closeBtn) closeBtn.click();
    """
    browser.page().runJavaScript(js)

def scrape_response():
    if not state["scraping_enabled"] or state["mode"] != "waiting":
        return
    js = """
    var msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
    msgs.length ? msgs[msgs.length-1].innerText : "";
    """
    browser.page().runJavaScript(js, handle_scrape)

def handle_scrape(text):
    if state["mode"] != "waiting":
        return
    t = (text or "").strip()
    if not t:
        state["stable"] = 0
        state["last_scraped"] = ""
        return
    if t == state["last_scraped"]:
        state["stable"] += 1
    else:
        state["last_scraped"] = t
        state["stable"] = 1
    if state["stable"] >= 2 and t != state["last_saved_assistant"]:
        print("\n--- ChatGPT Answer ---\n")
        print(t)
        state["last_saved_assistant"] = t
        history.append({"role": "assistant", "content": t})
        state["mode"] = "idle"
        ask_next()

def on_load_started():
    state["scraping_enabled"] = False

def on_load_finished(ok):
    QTimer.singleShot(300, lambda: None)
    state["scraping_enabled"] = True
    QTimer.singleShot(1200, auto_accept)

browser.loadStarted.connect(on_load_started)
browser.loadFinished.connect(on_load_finished)

timer = QTimer()
timer.timeout.connect(scrape_response)
timer.start(800)

browser.resize(1, 1)
browser.showMinimized()

ask_next()
sys.exit(app.exec())
