from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from time import sleep
from dotenv import dotenv_values

config = dotenv_values(".env")


class GithubAdminSession():
    def __init__(self, workerID, logger) -> None:
        self.logger = logger
        self.workerID = workerID
        options = self.getDriverOptions()
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(10)

        driver.get("https://github.com/login")

        driver.implicitly_wait(2)

        username = driver.find_element(by=By.ID, value="login_field")
        username.send_keys(config["GITHUB_ADMIN_USER_USERNAME"])
        pwd = driver.find_element(by=By.ID, value="password")
        pwd.send_keys(config["GITHUB_ADMIN_USER_PASSWORD"])
        sign_in_btn = driver.find_element(by=By.NAME, value="commit")
        sign_in_btn.click()


        self.driver = driver

    @staticmethod
    def getDriverOptions():
        options = Options()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", "/dev/null")
        options.set_preference(
            "browser.download.manager.showWhenStarting", False)

        return options

    def postTaskCleanup(self):
        print("started post task cleanup")
        # Removes download windows and other popups created by the task
        parent = self.driver.current_window_handle
        createdWindows = self.driver.window_handles
        for windowID in createdWindows:
            if windowID != parent:
                self.driver.switch_to.window(windowID)
                self.driver.close()

        # TODO: Sign out from actual OAuth client

        self.driver.get("https://stackoverflow.com/users/logout")
        self.driver.implicitly_wait(3)
        try:
            self.driver.find_element(
                by=By.CSS_SELECTOR, value="button.flex--item:nth-child(1)").click()
        except NoSuchElementException:
            self.logger.error(
                f'Could not find logout button to OAuth client on worker {self.workerID}')
        except:
            self.logger.criticial(
                f'Something went wrong when attempting OAuth logout on worker {self.workerID}')

        self.driver.implicitly_wait(3)
        self.driver.get("https://github.com/settings/applications")
        self.driver.implicitly_wait(3)
        try:
            self.driver.find_element(
                by=By.CSS_SELECTOR, value="summary.btn").click()
            fillInUserName = self.driver.find_element(
                by=By.ID, value="revoke-all-settings-oauth")
            fillInUserName.send_keys(config["GITHUB_ADMIN_USER_USERNAME"])
            fillInUserName.send_keys(Keys.ENTER)
        except NoSuchElementException:
            self.logger.error(
                f'Could not find elements used to reset Github OAuth apps on worker {self.workerID}')
        except:
            self.logger.criticial(
                f'Something went wrong when attempting to reset OAuth apps on worker {self.workerID}')

        sleep(4)

    def doTask(self, task):
        """
        self.driver.get("https://stackoverflow.com/users/login")
        self.driver.implicitly_wait(3)
        self.driver.find_element(
            by=By.CLASS_NAME, value="s-btn__github").click()

        """
        self.logger.info(f'Doing task on worker {self.workerID}')
        try:
            print("started")
            self.driver.get(task.url)
        except:
            print("excepted")
            self.logger.warn(
                f'Worker {self.workerID} had a problem loading the task {task.id}')
        print("done")
        if (self.driver.title == "Authorize application"):
            sleep(4)
            self.driver.find_element(
                by=By.ID, value="js-oauth-authorize-btn").click()
            sleep(4)
        self.postTaskCleanup()

    def quit(self):
        self.driver.quit()
