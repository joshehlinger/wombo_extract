import argparse
import sys

import wombo.styles
import wombo.extract


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
                        help=f'Styles: {wombo.styles.STYLES}')
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

    extractor = wombo.extract.Extractor(config)
    extractor.generate()


if __name__ == '__main__':
    sys.exit(main())
