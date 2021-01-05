import time
import os
import unittest

if __name__ == "__main__":
    from common import init, destroy, wait_for, take_screenshot
else:
    from .common import init, destroy, wait_for, take_screenshot


def graphics_test() -> None:
    from utility.constants import DATA_PATH, TEST_DATA_PATH
    import pyautogui


    # pick RRT algorithm
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'algorithm_new.png'), confidence=0.55)
    pyautogui.click(x + 150, y)
    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'rrt2.png'), confidence=0.9)
    pyautogui.click(x, y)

    x, y = pyautogui.locateCenterOnScreen(os.path.join(TEST_DATA_PATH, 'update.png'), confidence=0.5)
    pyautogui.click(x, y)

    wait_for('initialised.png')

    # run algo
    pyautogui.press('t')
    wait_for('done.png')

    take_screenshot("RRT_test_2D.png", threshold=350)


class GraphicsTestCase(unittest.TestCase):
    def test(self):
        try:
            this_dir = os.path.dirname(os.path.abspath(__file__))
            init(visualiser_args=['--maps', '{}/RRT_test_map_2D.py'.format(this_dir)])
            graphics_test()
        finally:
            destroy()


if __name__ == "__main__":
    GraphicsTestCase().test()
