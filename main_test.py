import pytest
from main import CMSAutomation
import mss
from PIL import Image


@pytest.fixture(scope="session")
def cms_automation():
    # 在此处实例化CMSAutomation并返回对象

    return CMSAutomation(
        [
            {
                "name": "测试1",
                "accno": "12345678",
                "password": "123456",
                "kcb": True,
                "xsb": True,
                "enabled": True,
            }
        ],
        "127.0.0.1:62025",
    )


def test_login(cms_automation):
    # 测试登录功能的测试用例
    pass


def test_submit_ipo(cms_automation):
    # 测试一键申购功能的测试用例
    pass


def test_submit_bond(cms_automation):
    # 测试申购债券功能的测试用例
    pass
    # 编写断言来验证申购债券是否成功
    # Add your assertions here


def test_send_screenshot(cms_automation):
    # 测试发送截图功能的测试用例
    cms_automation.send_screenshot()
    # 编写断言来验证发送截图是否成功
    # Add your assertions here


def test_start(cms_automation):
    # 测试启动CMSAutomation的测试用例
    cms_automation.start()
    # 编写断言来验证启动CMSAutomation是否成功
    # Add your assertions here


if __name__ == "__main__":
    pytest.main()
