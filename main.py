import tempfile
import time
import os
import uiautomator2 as u2
from uiautomator2.exceptions import UiObjectNotFoundError
import json
import logging as log
from pushover import Client
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

log_message = ""


def plog(message):
    global log_message
    log.info(message)
    log_message += message + "\n"


def env(str):
    return os.getenv(str)


def pushover_send(message, sound="pushover", img=None):
    client = Client(env("PUSHOVER_SECRET"), api_token=env("PUSHOVER_APP_TOKEN"))
    if img:
        with open(img, "rb") as image:
            client.send_message(message, attachment=image)
    else:
        client.send_message(message)


def start_emu_nox():
    import win32gui

    nox_path = env("NOX_PATH")
    title = env("NOX_TITLE")
    hwnd = win32gui.FindWindow(None, title)
    exists = hwnd > 0

    if not exists:
        plog("模拟器没有开启，正在打开模拟器。")
        os.system(f'start "" "{nox_path}Nox.exe" {env("NOX_INSTANCE")}')
        time.sleep(60)
    # 'C:\Program Files\Nox\bin\Nox.exe -clone:Nox_1'
    # netsh interface portproxy add v4tov4 62001 127.0.0.1 62001 需要管理员权限
    os.system("adb disconnect")
    os.system(f"adb connect 127.0.0.1:{env('NOX_ADB_PORT')}")


def stop_emu_nox():
    os.system("powershell kill -name nox*")


class CMSAutomation(object):
    def __init__(self, accounts, url):
        self.accounts = accounts
        self.current_account = self.accounts[0]
        self.url = url
        self.tmp_screenshots = []
        self.d = u2.connect(self.url)
        self.d.implicitly_wait(10.0)
        self.d.app_stop("com.cmschina.stock")
        self.d.app_start("com.cmschina.stock")
        self.watch_nags()
        try:
            self.d(
                text="交易", resourceId="com.cmschina.stock:id/main_toolbar_btn"
            ).click()
        except Exception as e:
            plog(str(e))
            pass

    def login(self, account):
        try:
            self.d(resourceId="com.cmschina.stock:id/ll_account").click(timeout=2)
            self.d(text="添加账号").click()
        except Exception:
            self.d(resourceId="com.cmschina.stock:id/tv_add_new_account").click()

        self.d(resourceId="com.cmschina.stock:id/et_account").set_text(account["accno"])
        self.d(resourceId="com.cmschina.stock:id/et_password").set_text(
            account["password"]
        )
        self.d(resourceId="com.cmschina.stock:id/btn_login").click()
        self.d(resourceId="com.cmschina.stock:id/label_jryk").wait()
        plog(f"登录账号{account['name']}成功")
        self.current_account = account

    def click_element(self, element):
        # 有些元素根据text是点击不到的，需要根据坐标点击

        self.d.click(element.center()[0], element.center()[1])

    def send_screenshot(self):
        tmp_file = tempfile.mktemp(suffix=".png")
        self.d.screenshot(tmp_file)
        self.tmp_screenshots.append(tmp_file)

    def get_combined_screenshot(self):
        images = [Image.open(x) for x in self.tmp_screenshots]
        widths, heights = zip(*(i.size for i in images))

        max_width = max(widths)
        total_height = sum(heights)

        new_img = Image.new("RGB", (max_width, total_height))

        y_offset = 0
        for img in images:
            new_img.paste(img, (0, y_offset))
            y_offset += img.height

        new_tmp_file = tempfile.mktemp(suffix=".png")
        new_img.save(new_tmp_file)
        return new_tmp_file

    def submit_ipo(self):
        self.d(text="新股新债").click()
        try:
            self.d(text="一键申购已选").wait()
            time.sleep(5)

            # 一键申购已选按钮不可用，尝试点击全选
            if not self.d(text="一键申购已选").info["enabled"]:
                self.d(textStartsWith="全选").click(timeout=3)
                plog("点击 全选 选择所有的新股")
                time.sleep(1)

            # 一键申购已选按钮还是不可用，说明没有新股
            if not self.d(text="一键申购已选").info["enabled"]:
                raise UiObjectNotFoundError()

            self.d(textStartsWith="一键申购已选").click(timeout=3)
            plog("点击 一键申购已选")

            time.sleep(3)
            # 一键申购无法用普通的方法找到坐标，只能用这种方法
            self.d.click(0.512, 0.944)

        except UiObjectNotFoundError:
            plog("没有发现可用的一键申购按钮")
            self.send_screenshot()
            self.back_to_main()
            return

        self.back_to_main()

        # 截图撤单界面的打新记录
        self.d(resourceId="com.cmschina.stock:id/element_tv", text="撤单").click(3)
        time.sleep(3)
        self.send_screenshot()
        self.back_to_main()

    def submit_bond(self):
        pass

    def watch_nags(self):
        nags = [
            "我已知晓",
            "我知道了",
            "不再提醒",
            "以后再说",
            "确认",
            "确定",
            "close",
            "关闭应用",
            "不用了",
            "忽略",
        ]
        for nag in nags:
            self.d.watcher.when(nag).click()
        self.d.watcher.start()

    def back_to_main(self):
        time.sleep(2)
        self.d.watcher.run()
        while not self.d(
            text="交易", resourceId="com.cmschina.stock:id/main_toolbar_btn"
        ).exists():
            self.d.click(0.064, 0.056)

        plog("已经到首页，不能再返回了。")

    def start(self):
        for account in self.accounts:
            self.login(account)
            self.submit_ipo()
            # self.submit_bond()


def main():
    # 读取json文件中的账号信息

    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(script_dir, "accounts.json"), "r", encoding="utf-8") as f:
        accounts = json.load(f)["accounts"]
    plog("开始执行打新股脚本。")
    pushover_send("开始执行打新股脚本。")
    # 实例化CMSAutomation

    try:
        for loop in range(10):
            try:
                start_emu_nox()
                cms = CMSAutomation(accounts, f"127.0.0.1:{env('NOX_ADB_PORT')}")
                cms.start()
                plog("打新股脚本执行完毕。")

                break
            except Exception as e:
                plog(f"打新股脚本执行出错。重试第{loop}次...{str(e)}")
                raise
    finally:
        pushover_send(log_message, img=cms.get_combined_screenshot())
        os.system("adb disconnect")
        # stop_emu_nox()


if __name__ == "__main__":
    main()
