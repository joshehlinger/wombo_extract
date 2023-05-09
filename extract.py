import argparse
import os
import sys
import time

import httpx
import yarl

from gestalt import generate_gestalt_image
from styles import STYLES

ASPECT_RATIOS = {
    '1:1': 'ratio_1',
    '16:9': 'ratio_16_9',
    '9:16': 'ratio_9_16',
    '4:3': 'ratio_4_3',
    '3:4': 'ratio_3_4',
    '960:1568': 'old_vertical_ratio',
}


class PollingTimeoutError(Exception):

    def __init__(self):
        super().__init__()


class Wombo:

    def __init__(self, config):
        self.base_url = yarl.URL('https://paint.api.wombo.ai/api/v2')
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

        self.input_image_id = config.input_image_id
        self.weight = config.input_image_id.upper()
        self.variation_id = config.variation_id

        self.ratio_string = config.ratio
        try:
            self.ratio = ASPECT_RATIOS[config.ratio]
        except KeyError:
            self.ratio = ASPECT_RATIOS['1:1']

        try:
            self.style = int(config.style)
        except ValueError:
            style_name = config.style.lower().strip()
            self.style = STYLES[style_name]

        style = None
        for name, idx in STYLES.items():
            if self.style == idx:
                style = name
                break
        if style is None:
            style = f'Style{self.style}'

        cleaned_prompt = config.prompt.replace('/', '_')[0:200]
        if self.style == 78:
            self.name = f"{cleaned_prompt}"
        else:
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

    def start_task(self, freq: int = 10):
        body = {'input_spec': {'display_freq': freq, 'style': self.style}}
        if self.variation_id:
            body['input_spec'].update({
                'gen_type': 'VARIATION',
                'input_image': {
                    'original_task_id': self.variation_id
                }
            })
        elif self.input_image_id:
            body['input_spec'].update({
                'prompt': self.prompt,
                'aspect_ratio': self.ratio,
                'input_image': {
                    'mediastore_id': self.input_image_id,
                    'weight': self.weight
                }
            })
        else:
            body['input_spec'].update({
                'prompt': self.prompt,
                'aspect_ratio': self.ratio,
            })

        url = self.base_url / 'tasks'
        resp = self.client.post(str(url), headers=self.headers, json=body)

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 401:
                raise RuntimeError(
                    "You probably don't have access to this style. Try "
                    "signing up for a premium account")
            raise
        return resp.json()['id']

    def check_task(self, task_id: str):
        url = self.base_url / 'tasks' / task_id
        resp = self.client.get(str(url), headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def handle_infinite_polling(self, start: float):
        print(f'Generating. Elapsed time: {int(time.time() - start)}s')
        print(f'Poll Count: {self.pending_count} out of {self.poll_count}')
        self.pending_count += 1
        if self.pending_count > self.poll_count:
            raise PollingTimeoutError()

    def create_new_directory(self):
        count = 0
        directory = self.directory
        while True:
            if os.path.exists(directory):
                count += 1
                directory = f'{self.directory} {count}'
            else:
                break
        self.directory = directory
        os.mkdir(self.directory)

    def generate(self):
        self.create_new_directory()

        textfile = open(f'{self.directory}/info.txt', 'w+')
        textfile.write(
            f'{self.prompt}\nstyle: {self.style}\naspect ratio: '
            f'{self.ratio_string}\ntime: {time.strftime("%Y-%m-%d %H:%M:%S")}'
            f'\n\nauth_url: {self.auth_url}\n\n')
        textfile.close()

        token = self.auth()
        self.headers = {'Authorization': f'bearer {token}'}

        start = time.time()
        max_poll_count_timeout = 0
        attempt = 1
        while attempt <= self.attempts:
            try:
                task_id = self.start_task()
                pending = True
                task = {}
                self.pending_count = 0
                while pending:
                    self.handle_infinite_polling(start)
                    time.sleep(self.poll_sleep)
                    task = self.check_task(task_id)
                    if task['state'] == 'failed' and task['is_nsfw'] is True:
                        pending = False
                    else:
                        pending = task['state'] != 'completed'

                urls = task['photo_url_list']
                if len(urls) == 0:
                    attempt = self.attempts
                    with open(f'{self.directory}/info.txt', 'a') as txt:
                        txt.write('\n\nProbably hit the NSFW filter')
                else:
                    url = urls[len(urls) - 1]
                    with open(f'{self.directory}/{format(attempt, "02")}.jpg',
                              'wb') as f:
                        f.write(httpx.get(url).content)
                    with open(f'{self.directory}/info.txt', 'a') as txt:
                        txt.write(f'\n\n{attempt}: {url}')

                attempt += 1

            except PollingTimeoutError:
                print(f'Too many polls! The limit is {self.poll_count}')
                max_poll_count_timeout += 1
                if max_poll_count_timeout >= self.max_poll_count_timeout:
                    raise RuntimeError('Max poll count timeout reached: '
                                       f'{self.max_poll_count_timeout}')

        if self.attempts > 1:
            generate_gestalt_image(self.directory, self.name)

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
                        default='78',
                        help=f'Styles: {STYLES}')
    parser.add_argument('--attempts',
                        dest='attempts',
                        type=int,
                        default=1,
                        help='num attempts'),
    parser.add_argument('--ratio',
                        dest='ratio',
                        default='1:1',
                        help='ratio (accepts "1:1", "4:3", "3:4", '
                        '"16:9", "9:16", or "960:1568")'),
    parser.add_argument('--variation_id',
                        dest='variation_id',
                        default="",
                        help='create variations of this task ID'),
    parser.add_argument('--input_image_id',
                        dest='input_image_id',
                        default="",
                        help='input image mediastore ID'),
    parser.add_argument('--weight',
                        dest='weight',
                        default="MEDIUM",
                        help='input image weight (accepts "LOW", '
                        '"MEDIUM", "HIGH")'),
    parser.add_argument('--sleep',
                        dest='sleep',
                        type=int,
                        default=6,
                        help='Seconds to sleep between GET polls')
    parser.add_argument('--poll_count',
                        dest='poll_count',
                        type=int,
                        default=6,
                        help='Number of intervals to wait for')
    parser.add_argument('--max_poll_count_timeout',
                        dest='max_poll_count_timeout',
                        type=int,
                        default=36,
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
