# Wombo Extractor
Simple silly CLI script to pull the downloadable links out of the wombo dream creator. 
Very rough around the edges right now

Wombo Dream: https://app.wombo.art/

## Development
`python -m venv env`

`source env/bin/activate`

`pip install -r requirements.txt`


## Usage
`python extract.py --email=MyName@foo.bar --password=Pass --prompt="test foo bar"`

Note: You'll need to double-quote the `prompt` if it has spaces