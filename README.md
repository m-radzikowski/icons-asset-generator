# Icons Asset Generator for OmniGraffle and diagrams.net

Convert SVG images into:

- [OmniGraffle](https://www.omnigroup.com/omnigraffle/) Stencil
- [diagrams.net](https://diagrams.net/)
  ([formerly draw.io](https://www.diagrams.net/blog/move-diagrams-net)) library

Features:

- parametrize connection points (magnets)
- filter images by name
- format icon names

See [diagrams-aws-icons](https://github.com/m-radzikowski/diagrams-aws-icons)
with generated AWS Architecture Icons library for diagrams.net.

Idea based on script from
[AWS-OmniGraffle-Stencils](https://github.com/davidfsmith/AWS-OmniGraffle-Stencils/)

## Usage

Requires Python 3.8+ and [Poetry](https://python-poetry.org/).

Install dependencies in virtual env:

```bash
poetry install
```

Run:

```bash
poetry run icons-asset-generator \
    --path ./icons-directory [<common-args>] \
    <target-application> [<application-args>]
```

where `<target-application>` is one of:

- `diagrams.net`
- `omnigraffle`

### Common options

- `--path` - input files directory path
- `--output` - output directory path (default: `./library`)
- `--filename-includes` - strings to filter image file name by, taking only those which contains them all; accepts multiple arguments
- `--filename-excludes` - strings to filter image file name by, taking only those which do not contain any of them; accepts multiple arguments
- `--image-name-remove` - strings to be removed from image file name (default: `. - _`); accepts multiple arguments
- `--library-name-remove` - strings to be removed from library file name (default: `. - _`); accepts multiple arguments
- `--no-vertex-magnets` - don't create connection points on vertices (corners)
- `--side-magnets` - number of connection points for each side (default: `5`)
- `--labels` - add label with name to the images
- `--help` - display help

All SVG files from the given `path` will be added to the output asset, recursively.

If you provide arguments accepting multiple arguments, put the `--path` argument last so the parser knows where arguments stop
and parses `<target-application>` parameter correctly.

### Diagrams.net specific options

- `--size` - resize images to target size; accepts argument in format `TYPE=NUMBER` where `TYPE` is one of `width`, `height`, `longest`

### OmniGraffle specific options

- `--text-output` - write OmniGraffle data file as text instead of binary

If SVG files are grouped into directories, each root-level directory will become
a separate group in the output Stencil.

For example, this structure:

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

would produce a Stencil with `Group 1` with 3 icons and `Group 2` with 2 icons.

### Example: AWS Architecture Icons

To generate icons from [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/)
download SVG zip file
(example: [Asset-Package_04302022](https://d1.awsstatic.com/webteam/architecture-icons/q2-2022/Asset-Package_04302022.e942f826cd826cfa2d32455f3a7973ad4b92eb6a.zip))
and unpack it.

Run:

```bash
poetry run icons-asset-generator \
    --path "./Asset-Package_04302022" \
    --filename-includes _48 \
    --filename-excludes Dark \
    --image-name-remove Light Arch_ Res_ _48 . - _  \
    --library-name-remove  . - _ \
    diagrams.net
```

Open [diagrams.net](https://app.diagrams.net/?splash=0)
and [load created asset](https://www.diagrams.net/blog/custom-libraries)
from the `./library` directory.
