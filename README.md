# diagrams.net library creator

Create diagrams.net (draw.io) library from SVG images.

## Usage

### AWS Architecture Icons example

To generate icons from [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/)
download SVG zip file
(example: [AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911](https://d1.awsstatic.com/webteam/architecture-icons/Q32020/AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911.478ff05b80f909792f7853b1a28de8e28eac67f4.zip))
and unpack it.

To create a separate library for each of the icons category:

```bash
poetry run drawio-svg-icons \
    --svg-dir "./AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911/AWS-Architecture-Service-Icons_20200911" \
    --filename-includes _48 \
    --image-name-remove . - _ Arch _48 \
    --library-name-remove . - _ Arch
```

Add `--single-library` flag and remove `--library-name-remove` parameter
to create a single output library with all the icons.

## Development

Requires Python 3.8+ and [Poetry](https://python-poetry.org/).

Install dependencies in virtual env:

```bash
poetry shell
poetry install
```

Get virtual env path for the IDE:

```bash
poetry env info -p
```

Run script:

```bash
poetry run drawio-svg-icons
```
