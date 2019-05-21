# OCR-D/core

> Python modules implementing [OCR-D specs](https://github.com/OCR-D/spec) and related tools

[![image](https://img.shields.io/pypi/v/ocrd.svg)](https://pypi.org/project/ocrd/)
[![image](https://travis-ci.org/OCR-D/core.svg?branch=master)](https://travis-ci.org/OCR-D/core)
[![image](https://circleci.com/gh/OCR-D/core.svg?style=svg)](https://circleci.com/gh/OCR-D/core)
[![image](https://scrutinizer-ci.com/g/OCR-D/core/badges/build.png?b=master)](https://scrutinizer-ci.com/g/OCR-D/core)
[![Docker Automated build](https://img.shields.io/docker/automated/ocrd/pyocrd.svg)](https://hub.docker.com/r/ocrd/core/tags/)
[![image](https://codecov.io/gh/OCR-D/core/branch/master/graph/badge.svg)](https://codecov.io/gh/OCR-D/core)
[![image](https://scrutinizer-ci.com/g/OCR-D/core/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/OCR-D/core)
[![image](https://img.shields.io/lgtm/alerts/g/OCR-D/core.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/OCR-D/core/alerts/)

[![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/OCR-D/Lobby)


<!-- BEGIN-MARKDOWN-TOC -->
* [Introduction](#introduction)
* [Modules](#modules)
	* [ocrd_utils](#ocrd_utils)
	* [ocrd_models](#ocrd_models)
	* [ocrd_modelfactory](#ocrd_modelfactory)
	* [ocrd_validators](#ocrd_validators)
	* [ocrd](#ocrd)
* [Testing](#testing)
* [See Also](#see-also)

<!-- END-MARKDOWN-TOC -->

## Introduction

This repository contains the python modules that form the base for tools within the
[OCR-D ecosphere](https://github.com/topics/ocr-d).

All modules are also published to [PyPI](https://pypi.org/search/?q=ocrd).

The easiest way to install is via `pip`:

```sh
pip install ocrd

# or just the functionality you need, e.g.

pip install ocrd_modelfactory
```

## Modules

### ocrd_utils

Contains helpers and utilities, e.g. for unified logging, path normalization etc.

See [README for `ocrd_utils`](./ocrd_utils/README.md) for further information.

### ocrd_models

Contains file format wrappers for PAGE-XML, METS, EXIF metadata etc.

See [README for `ocrd_models`](./ocrd_models/README.md) for further information.

### ocrd_modelfactory

Code to instantiate [models](#ocrd-models) from existing data.

See [README for `ocrd_modelfactory`](./ocrd_modelfactory/README.md) for further information.

### ocrd_validators

Schemas and routines for validating BagIt, `ocrd-tool.json`, workspaces, METS, page, CLI parameters etc.

See [README for `ocrd_validators`](./ocrd_validators/README.md) for further information.

### ocrd

Contains all of the above and in addition decorators for creating OCR-D processors and CLI.

Also contains the command line tool `ocrd`.

See [README for `ocrd`](./ocrd/README.md) for further information.

## Testing

Download assets (`make assets`)

Test with local files: `make test`

- Test with local asset server:
  - Start asset-server: `make asset-server`
  - `make test OCRD_BASEURL='http://localhost:5001/'`

- Test with remote assets:
  - `make test OCRD_BASEURL='https://github.com/OCR-D/assets/raw/master/data/'`

## See Also

  - [OCR-D Specifications](https://ocr-d.github.io) ([Repo](https://github.com/ocr-d/spec))
  - [OCR-D Documentation](https://ocr-d.github.io/docs) ([Repo](https://github.com/ocr-d/docs))
