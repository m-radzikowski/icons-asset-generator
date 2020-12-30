# diagrams.net shapes library creator

Create [diagrams.net](https://diagrams.net/)
([formerly draw.io](https://www.diagrams.net/blog/move-diagrams-net))
shape libraries from SVG images.

Features:

- create single or multiple separated libraries by directory
- parametrize shape connection points
- filter input images by name
- adjust shape size
- generate links to load hosted libraries

## Usage

Requires Python 3.8+.

```
usage: diagrams-shapes-library [-h] [--svg-dir PATH] [--output-dir PATH] [--size TYPE=VALUE] [--filename-includes VALUE [VALUE ...]] [--filename-excludes VALUE [VALUE ...]] [--image-name-remove VALUE [VALUE ...]]
                               [--library-name-remove VALUE [VALUE ...]] [--single-library] [--no-vertex-magnets] [--side-magnets COUNT] [--labels] [--base-url URL]

Create diagrams.net shape libraries from SVG images.

optional arguments:
  -h, --help            show this help message and exit
  --svg-dir PATH        svg files directory path (default: ./svg)
  --output-dir PATH     path to the output directory (default: ./library)
  --size TYPE=VALUE     resize images to target size; allowed TYPE values: width, height, longest
  --filename-includes VALUE [VALUE ...]
                        strings to filter image file name by, taking only those which contains them all
  --filename-excludes VALUE [VALUE ...]
                        strings to filter image file name by, taking only those which do not contain any of them
  --image-name-remove VALUE [VALUE ...]
                        strings to be removed and replaced by spaces from image file name (default: . - _)
  --library-name-remove VALUE [VALUE ...]
                        strings to be removed and replaced by spaces from library file name (default: . - _)
  --single-library      create single output library
  --no-vertex-magnets   don't create connection points on vertices (corners)
  --side-magnets COUNT  number of connection points for each side (default: 5)
  --labels              add label with name to images
  --base-url URL        base URL to generate link(s) to open libraries in diagrams.net
```

Input files are taken from the given location (`./svg` by default).

They can be given in a flat structure:

```
svg/
├── icon1.svg
├── icon2.svg
└── icon3.svg
```

or grouped into directories:

```
svg/
├── Group 1/
│   ├── icon1.svg
│   ├── icon2.svg
│   ├── icon3.svg
└── Group 2/
    ├── icon4.svg
    └── Subgroup
        └── icon5.svg
```

If files are grouped into directories, each root-level directory will become
a separate library file (unless `--single-library` flag is given).
In the above example two libraries would be produced:
`Group 1` with 3 icons and `Group 2` with 2 icons.

Use include and exclude parameters to filter images based on the name.

### Example: AWS Architecture Icons

To generate icons from [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/)
download SVG zip file
(example: [AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911](https://d1.awsstatic.com/webteam/architecture-icons/Q32020/AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911.478ff05b80f909792f7853b1a28de8e28eac67f4.zip))
and unpack it.

To create a separate library for each of the service icons category:

```bash
poetry run diagrams-shapes-library \
    --svg-dir "./AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911/AWS-Architecture-Service-Icons_20200911" \
    --filename-includes _48 \
    --image-name-remove Arch_ _48 . - _  \
    --library-name-remove Arch_ . - _ \
    --size height=50
```

To create one library with all resource icons:

```bash
poetry run diagrams-shapes-library \
    --svg-dir "./AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911/AWS-Architecture-Resource-Icons_20200911" \
    --filename-includes _48_Light \
    --image-name-remove Res_ _48_Light . - _  \
    --size height=50 --single-library
```

Open [diagrams.net](https://app.diagrams.net/?splash=0)
and [load created libraries](https://www.diagrams.net/blog/custom-libraries)
from the `./library` directory.

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
poetry run diagrams-shapes-library
```
