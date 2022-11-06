import argparse
import math
import os
import sys
import time

import httpx
import yarl
from PIL import Image

# Note: Some of these styles only work for premium accounts
STYLES = {
    'synthwave': 1,
    'ukiyoe': 2,
    'no style': 3,
    'steampunk': 4,
    'fantasy art': 5,
    'bibrant': 6,
    'hd': 7,
    'pastel': 8,
    'psychic': 9,
    'dark fantasy': 10,
    'mystical': 11,
    'festive': 12,
    'baroque': 13,
    'etching': 14,
    's.dali': 15,
    'wuhtercuhler': 16,
    'provenance': 17,
    'rose gold': 18,
    'moonwalker': 19,
    'blacklight': 20,
    'psychedelic': 21,
    'ghibli': 22,
    'love': 24,
    'death': 25,
    'robots': 26,
    'radioactive': 27,
    'melancholic': 28,
    'transitory': 29,
    'aquatic': 30,
    'toasty': 31,
    'realistic': 32,
    'van gogh': 33,
    'arcane': 34,
    'throwback': 35,
    'daydream': 36,
    'ink': 38,
    'pandora': 39,
    'malevolent': 40,
    'street art': 41,
    'unrealistic': 42,
    'vibrance': 43
}


class PollingTimeoutError(Exception):

    def __init__(self):
        super().__init__()


class Wombo:

    def __init__(self, config):
        self.base_url = yarl.URL('https://paint.api.wombo.ai/api')
        self.auth_url = yarl.URL(
            'https://www.googleapis.com/identitytoolkit/v3/relyingparty/'
            'verifyPassword?key=AIzaSyDCvp5MTJLUdtBYEKYWXJrlLzu1zuKM6Xw')
        self.headers = {}

        self.email = config.email
        self.password = config.password
        self.prompt = config.prompt
        self.attempts = config.attempts
        self.poll_sleep = config.sleep
        self.poll_count = config.poll_count
        self.max_poll_count_timeout = config.max_poll_count_timeout
        self.pending_count = 0

        try:
            self.style = int(config.style)
        except ValueError:
            style_name = config.style.lower().strip()
            self.style = STYLES[style_name]

        style = None
        for name, idx in STYLES.items():
            if self.style == idx:
                style = name.replace(' ', '_')
                break
        if style is None:
            style = f'Style{self.style}'
        cleaned_prompt = config.prompt.replace('/', '_')
        self.name = f"{cleaned_prompt}  ({style.capitalize()})"
        self.directory = f"./images/{self.name}"
        self.client = httpx.Client(timeout=10.0)

    def auth(self) -> str:
        auth_body = {
            'email': self.email,
            'password': self.password,
            'returnSecureToken': True
        }
        resp = self.client.post(str(self.auth_url), json=auth_body)
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
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 401:
                raise RuntimeError(
                    "You probably don't have access to this style. Try "
                    "signing up for a premium account")
            raise

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
        total_width = max(widths) * 4
        max_height = max(heights) * int(math.ceil(len(widths) / 4))

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

        new_im.save(f'./images/{self.name}.jpg', quality=100)

    def handle_infinite_polling(self, start: float):
        print(f'Generating. Elapsed time: {int(time.time() - start)}s')
        print(f'Poll Count: {self.pending_count}')
        self.pending_count += 1
        if self.pending_count > self.poll_count:
            raise PollingTimeoutError()

    def create_new_directory(self):
        new_dir_found = False
        count = 0
        directory = self.directory
        while not new_dir_found:
            if os.path.exists(directory):
                count += 1
                directory = f'{self.directory} {count}'
            else:
                new_dir_found = True
        self.directory = directory
        os.mkdir(self.directory)

    def generate(self):
        self.create_new_directory()
        token = self.auth()
        self.headers = {
            'Authorization': f'bearer {token}',
            'Content-Type': 'text/plain;charset=UTF-8',
            'service': 'Dream',
            'Origin': 'https://app.wombo.art',
            'Referer': 'https://app.wombo.art/'
        }
        start = time.time()
        max_poll_count_timeout = 0
        attempt = 1
        while attempt <= self.attempts:
            try:
                task_id = self.get_task()
                self.start_task(task_id, self.prompt, self.style)

                pending = True
                task = {}
                self.pending_count = 0
                while pending:
                    self.handle_infinite_polling(start)
                    time.sleep(self.poll_sleep)
                    task = self.check_task(task_id)
                    pending = task['state'] != 'completed'
                print(task['result']['final'])
                with open(f'{self.directory}/{format((attempt), "02")}.jpg',
                          'wb') as f:
                    f.write(httpx.get(task['result']['final']).content)
                    attempt += 1
            except PollingTimeoutError:
                print(f'Too many polls! The limit is {self.poll_count}')
                max_poll_count_timeout += 1
                if max_poll_count_timeout >= self.max_poll_count_timeout:
                    raise RuntimeError('Max poll count timeout reached: '
                                       f'{self.max_poll_count_timeout}')

        if self.attempts > 1:
            self.generate_gestalt_image()
        self.client.close()


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', dest='email', help='email')
    parser.add_argument('--password', dest='password', help='password')
    parser.add_argument('--prompt',
                        dest='prompt',
                        default='yarn doodle goat',
                        help='Wombo string prompt (put in double quotes!)')
    parser.add_argument('--style',
                        dest='style',
                        default='32',
                        help=f'Styles: {STYLES}')
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
    parser.add_argument('--poll_count',
                        dest='poll_count',
                        type=int,
                        default=5,
                        help='Number of intervals to wait for')
    parser.add_argument('--max_poll_count_timeout',
                        dest='max_poll_count_timeout',
                        type=int,
                        default=24,
                        help='Maximum number of times allowed to poll count '
                        'timeout before exit')
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
