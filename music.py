import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from voice import speak
import urllib.parse

driver = None
current_song = ""

def get_driver():
    global driver

    if driver is None:
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--autoplay-policy=no-user-gesture-required")

        driver = webdriver.Chrome(options=options)

    return driver

def play_music(query: str):
    global driver, current_song

    current_song = query
    speak(f"Playing {query}")
    # set_song(query)

    driver = get_driver()
    query = urllib.parse.quote(query)
    driver.get(f"https://www.youtube.com/results?search_query={query}")

    time.sleep(3)

    try:
        videos = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
        if videos:
            driver.execute_script("arguments[0].click();", videos[0])
            time.sleep(2)
        else:
            speak("No video found")
    except Exception as e:
        print(e)
        speak("Error playing song")

def play_playlist(command: str):
    play_music(command + " playlist")

def pause_song():
    if driver:
        driver.find_element(By.TAG_NAME, "body").send_keys("k")

def resume_song():
    speak("Resuming music")
    if driver:
        driver.find_element(By.TAG_NAME, "body").send_keys("k")

def next_song():
    try:
        btn = driver.find_element(By.CLASS_NAME, "ytp-next-button")
        driver.execute_script("arguments[0].click();", btn)
    except:
        speak("Next not available")

def previous_song():
    try:
        btn = driver.find_element(By.CLASS_NAME, "ytp-prev-button")
        driver.execute_script("arguments[0].click();", btn)
    except:
        driver.find_element(By.TAG_NAME, "body").send_keys("0")

def close_music():
    global driver
    try:
        if driver:
            driver.quit()
    except:
        pass
    driver = None