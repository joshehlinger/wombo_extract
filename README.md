# Wombo Extractor
Simple CLI script to pull the downloadable links out of the wombo dream creator.

Wombo Dream: https://app.wombo.art/

## Development
`python -m venv env`

`source env/bin/activate`

`pip install -r requirements.txt`


## Usage
`python extract.py --email=email@foo.bar --password=p@assword --prompt="test foo bar" --attempts=5`

Note: You'll need to double-quote the `prompt` if it has spaces

Images are found in /images