import argparse
import sys
import time

import httpx
import yarl


class Wombo:
    def __init__(self, config):
        self.base_url = yarl.URL('https://app.wombo.art/api')
        self.auth_url = yarl.URL(
            'https://www.googleapis.com/identitytoolkit/v3/relyingparty/'
            'verifyPassword?key=AIzaSyDCvp5MTJLUdtBYEKYWXJrlLzu1zuKM6Xw')
        self.headers = {}
        self.poll_sleep = 3

        self.email = config.email
        self.password = config.password
        self.prompt = config.prompt
        self.style = config.style

    def auth(self) -> str:
        auth_body = {
            'email': self.email,
            'password': self.password,
            'returnSecureToken': True
        }
        resp = httpx.post(str(self.auth_url), json=auth_body)
        body = resp.json()
        id_token = body['idToken']
        refresh_token = body['refreshToken']

        return id_token

    def get_task(self, client) -> str:
        task_url = self.base_url / 'tasks'
        resp = client.post(str(task_url), headers=self.headers)
        resp.raise_for_status()
        return resp.json()['id']

    def start_task(self, client, task_id, prompt, style, freq=10):
        body = {
            'input_spec': {
                'prompt': prompt,
                'style': style,
                'display_freq': freq
            }
        }
        url = self.base_url / 'tasks' / task_id
        resp = client.put(str(url), headers=self.headers, json=body)
        resp.raise_for_status()

    def check_task(self, client, task_id):
        url = self.base_url / 'tasks' / task_id
        resp = client.get(str(url), headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def generate(self):
        token = self.auth()
        with httpx.Client(timeout=10.0) as client:
            self.headers = {
                'Authorization': f'bearer {token}',
                'Content-Type': 'text/plain;charset=UTF-8',
                'service': 'Dream',
                'Origin': 'https://app.wombo.art',
                'Referer': 'https://app.wombo.art/'
            }
            task_id = self.get_task(client)
            self.start_task(client, task_id, self.prompt, self.style)
            pending = True
            while pending:
                print('generating...')
                time.sleep(self.poll_sleep)
                task = self.check_task(client, task_id)
                pending = task['state'] != 'completed'
            print(task['result']['final'])


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--email',
                        dest='email',
                        help='email')
    parser.add_argument('--password',
                        dest='password',
                        help='password')
    parser.add_argument('--prompt',
                        dest='prompt',
                        default='foobar',
                        help='Wombo string prompt (put in double quotes!)')
    parser.add_argument('--style',
                        dest='style',
                        type=int,
                        default=3,
                        help='Numeric style integer')
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