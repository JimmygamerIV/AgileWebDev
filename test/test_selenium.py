import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
import time 

pytestmark = pytest.mark.selenium

def _get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gcm")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return options

def _chrome_available():
    try:
        driver = webdriver.Chrome(options=_get_chrome_options())
        driver.quit()
        return True
    except (WebDriverException, Exception):
        return False

@pytest.fixture(autouse=True, scope="module")
def _skip_when_chrome_missing():
    if not _chrome_available():
        pytest.skip(
            "Chrome WebDriver is not available in this environment; selenium tests are skipped.",
            allow_module_level=False,
        )

@pytest.fixture
def driver():
    driver = webdriver.Chrome(options=_get_chrome_options())
    yield driver
    driver.quit()


class TestRobustUniMapFlows:

    def test_signin_page_loads_correctly(self, live_server, driver):
        driver.maximize_window()
        driver.get(f"{live_server.url}/signin")
        
        assert "signin" in driver.current_url
        
        username_present = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        assert username_present.is_displayed()
        

        submit_btn_present = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
        assert submit_btn_present is not None


    def test_signup_flow_with_dynamic_user(self, live_server, driver):
        driver.maximize_window()
        driver.get(f"{live_server.url}/signup")
        
        timestamp = int(time.time())
        unique_user = f"uwa_user_{timestamp}"
        unique_email = f"student_{timestamp}@student.uwa.edu.au"
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(unique_user)
        driver.find_element(By.NAME, "nickname").send_keys("Agile Tester")
        driver.find_element(By.NAME, "email").send_keys(unique_email)
        driver.find_element(By.NAME, "password").send_keys("TestPass123")
        driver.find_element(By.NAME, "confirm_password").send_keys("TestPass123")
        
        submit_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@type='submit'] | //input[@type='submit']"))
        )
        driver.execute_script("arguments[0].click();", submit_btn)
        

        WebDriverWait(driver, 10).until(EC.url_to_be(f"{live_server.url}/"))
        assert driver.current_url == f"{live_server.url}/"


    def test_signup_password_mismatch_error(self, live_server, driver):

        driver.maximize_window()
        driver.get(f"{live_server.url}/signup")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("error_user")
        driver.find_element(By.NAME, "email").send_keys("error@student.uwa.edu.au")
        driver.find_element(By.NAME, "password").send_keys("TestPass123")
        driver.find_element(By.NAME, "confirm_password").send_keys("WrongPass789")
        
        submit_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@type='submit'] | //input[@type='submit']"))
        )
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(1) 
        assert "signup" in driver.current_url
        


    def test_forgot_password_validation_with_invalid_email(self, live_server, driver):
        driver.maximize_window()
        driver.get(f"{live_server.url}/forgot_password")
        
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys("gmail_user@gmail.com")
        

        submit_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@type='submit'] | //input[@type='submit']"))
        )
        driver.execute_script("arguments[0].click();", submit_btn)
        
        assert "reset_password" not in driver.current_url


    def test_anonymous_user_redirected_from_add_event(self, live_server, driver):
        driver.maximize_window()
        driver.get(f"{live_server.url}/add-event")
        
        WebDriverWait(driver, 10).until(
            lambda d: "signin" in d.current_url or "login" in d.current_url
        )
        assert "add-event" not in driver.current_url