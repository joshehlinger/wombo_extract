import argparse
import math
import os
import shutil
import sys
import time

import httpx
import yarl
from PIL import Image


class Wombo:

    def __init__(self, config):
        self.base_url = yarl.URL('https://app.wombo.art/api')
        self.auth_url = yarl.URL(
            'https://www.googleapis.com/identitytoolkit/v3/relyingparty/'
            'verifyPassword?key=AIzaSyDCvp5MTJLUdtBYEKYWXJrlLzu1zuKM6Xw')
        self.headers = {}

        self.email = config.email
        self.password = config.password
        self.prompt = config.prompt
        self.style = config.style
        self.attempts = config.attempts
        self.poll_sleep = config.sleep

        self.directory = f"./images/{config.prompt.replace(' ', '_')}"
        self.client = httpx.Client(timeout=10.0)

    def auth(self) -> str:
        auth_body = {
            'email': self.email,
            'password': self.password,
            'returnSecureToken': True
        }
        resp = httpx.post(str(self.auth_url), json=auth_body)
        body = resp.json()
        id_token = body['idToken']

        return id_token

    def get_task(self) -> str:
        task_url = self.base_url / 'tasks'
        resp = self.client.post(str(task_url), headers=self.headers)
        resp.raise_for_status()
        return resp.json()['id']

    def start_task(self, task_id: str, prompt: str, style: int, freq=10):
        body = {
            'input_spec': {
                'prompt': prompt,
                'style': style,
                'display_freq': freq
            }
        }
        url = self.base_url / 'tasks' / task_id
        resp = self.client.put(str(url), headers=self.headers, json=body)
        resp.raise_for_status()

    def check_task(self, task_id: str):
        url = self.base_url / 'tasks' / task_id
        resp = self.client.get(str(url), headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def generate_gestalt_image(self):
        all_images = [
            f for f in os.listdir(self.directory)
            if os.path.isfile(os.path.join(self.directory, f))
        ]
        all_images.sort()
        images = [Image.open(f'{self.directory}/{x}') for x in all_images]
        widths, heights = zip(*(i.size for i in images))
        num_images = len(widths)
        rows = int(math.ceil(num_images / 4))
        total_width = max(widths) * 4
        max_height = max(heights) * rows

        new_im = Image.new('RGB', (total_width, max_height))

        x_offset = 0
        y_offset = 0
        row_count = 0
        for im in images:
            new_im.paste(im, (x_offset, y_offset))
            x_offset += im.size[0]
            row_count += 1
            if row_count == 4:
                x_offset = 0
                y_offset += im.size[1]
                row_count = 0

        new_im.save(f'{self.directory}/FINAL.jpg')

    def generate(self):
        try:
            os.mkdir(self.directory)
        except OSError:
            shutil.rmtree(self.directory)
            os.mkdir(self.directory)

        token = self.auth()
        self.headers = {
            'Authorization': f'bearer {token}',
            'Content-Type': 'text/plain;charset=UTF-8',
            'service': 'Dream',
            'Origin': 'https://app.wombo.art',
            'Referer': 'https://app.wombo.art/'
        }
        start = time.time()
        for x in range(1, self.attempts + 1):
            task_id = self.get_task()
            self.start_task(task_id, self.prompt, self.style)

            pending = True
            task = {}
            while pending:
                print(f'Generating. Elapsed time: {int(time.time() - start)}s')
                time.sleep(self.poll_sleep)
                task = self.check_task(task_id)
                pending = task['state'] != 'completed'
            print(task['result']['final'])
            with open(f'{self.directory}/{x}.jpg', 'wb') as f:
                f.write(httpx.get(task['result']['final']).content)

        if self.attempts > 1:
            self.generate_gestalt_image()
        self.client.close()


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', dest='email', help='email')
    parser.add_argument('--password', dest='password', help='password')
    parser.add_argument('--prompt',
                        dest='prompt',
                        default='foobar',
                        help='Wombo string prompt (put in double quotes!)')
    parser.add_argument('--style',
                        dest='style',
                        type=int,
                        default=3,
                        help='Numeric style integer')
    parser.add_argument('--attempts',
                        dest='attempts',
                        type=int,
                        default=1,
                        help='num attempts'),
    parser.add_argument('--sleep',
                        dest='sleep',
                        type=int,
                        default=5,
                        help='Seconds to sleep between GET polls')
    return parser


def main(args=None):
    parser = arg_parser()
    config = parser.parse_args(args=args)
    if config.email is None or config.password is None:
        print('Email and Password are required!')
        return 1

    wombo = Wombo(config)
    wombo.generate()


if __name__ == '__main__':
    sys.exit(main())
