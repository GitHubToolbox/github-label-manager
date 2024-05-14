<!-- markdownlint-disable -->
<p align="center">
    <a href="https://github.com/GitHubToolbox/">
        <img src="https://cdn.wolfsoftware.com/assets/images/github/organisations/githubtoolbox/black-and-white-circle-256.png" alt="GitHubToolbox logo" />
    </a>
    <br />
    <a href="https://github.com/GitHubToolbox/github-label-manager/actions/workflows/cicd.yml">
        <img src="https://img.shields.io/github/actions/workflow/status/GitHubToolbox/github-label-manager/cicd.yml?branch=master&label=build%20status&style=for-the-badge" alt="Github Build Status" />
    </a>
    <a href="https://github.com/GitHubToolbox/github-label-manager/blob/master/LICENSE.md">
        <img src="https://img.shields.io/github/license/GitHubToolbox/github-label-manager?color=blue&label=License&style=for-the-badge" alt="License">
    </a>
    <a href="https://github.com/GitHubToolbox/github-label-manager">
        <img src="https://img.shields.io/github/created-at/GitHubToolbox/github-label-manager?color=blue&label=Created&style=for-the-badge" alt="Created">
    </a>
    <br />
    <a href="https://github.com/GitHubToolbox/github-label-manager/releases/latest">
        <img src="https://img.shields.io/github/v/release/GitHubToolbox/github-label-manager?color=blue&label=Latest%20Release&style=for-the-badge" alt="Release">
    </a>
    <a href="https://github.com/GitHubToolbox/github-label-manager/releases/latest">
        <img src="https://img.shields.io/github/release-date/GitHubToolbox/github-label-manager?color=blue&label=Released&style=for-the-badge" alt="Released">
    </a>
    <a href="https://github.com/GitHubToolbox/github-label-manager/releases/latest">
        <img src="https://img.shields.io/github/commits-since/GitHubToolbox/github-label-manager/latest.svg?color=blue&style=for-the-badge" alt="Commits since release">
    </a>
    <br />
    <a href="https://github.com/GitHubToolbox/github-label-manager/blob/master/.github/CODE_OF_CONDUCT.md">
        <img src="https://img.shields.io/badge/Code%20of%20Conduct-blue?style=for-the-badge" />
    </a>
    <a href="https://github.com/GitHubToolbox/github-label-manager/blob/master/.github/CONTRIBUTING.md">
        <img src="https://img.shields.io/badge/Contributing-blue?style=for-the-badge" />
    </a>
    <a href="https://github.com/GitHubToolbox/github-label-manager/blob/master/.github/SECURITY.md">
        <img src="https://img.shields.io/badge/Report%20Security%20Concern-blue?style=for-the-badge" />
    </a>
    <a href="https://github.com/GitHubToolbox/github-label-manager/issues">
        <img src="https://img.shields.io/badge/Get%20Support-blue?style=for-the-badge" />
    </a>
</p>

## Overview

This script is designed to allow you to manage the labels on your GitHub repositories.

Keeping all your labels consistent makes it easier to work across multiple repositories (and organisations)

We currently manage over 100 repositories across more than 15 organisations so it is important to reduce
any friction when moving between project.

To get you started we have also included a copy of the config that we use for all of the repositories we manage,
you can find that in the [config](config) directory. In there you will find a copy of the labels in both
[JSON](config/labels.json) and [YAML](config/labels.yml) format.

## Command Line Usage

```shell
usage: github-label-manager [-h] [-d] [-v] [-j | -y] [-t TOKEN] -f FILENAME [-u USER | -o ORG | -r REPO]

Setup labels on git repository.

flags:
  -h, --help            show this help message and exit.
  -d, --dry-run         Perform a dry run (default: False)
  -v, --validate        Validate local labels (default: False)

mutually exclusive flags:
  -j, --json            JSON formatted config file (default: True)
  -y, --yaml            YAML formatted config file (default: False)

selective:
  -t TOKEN, --token TOKEN
                        GitHub token (needed for everything except -v/--validate) (default: None)

required:
  -f FILENAME, --filename FILENAME
                        File containing labels (default: None)

mutually exclusive:
  -u USER, --user USER  Specify username (default: None)
  -o ORG, --org ORG     Specify organization (default: None)
  -r REPO, --repo REPO  Specify repository (default: None)
```

## Examples

### Validate the labels config file
```shell
$ github-label-manager -f config/labels.json -v
```

### Update a specific repository

```shell
$ github-label-manager -f config/labels.json -t <PAT> -r <Repository>
```
> Repository is in the format of organization/repo_full_name E.g. GitHubToolbox/github-label-manager

### Update all repositories for a given organization
```shell
$ github-label-manager -f config/labels.json -t <PAT> -o <Organisation>
```

### Update all repositories for a given user
```shell
$ github-label-manager -f config/labels.json -t <PAT> -u <username>
```

### Dry Runs
You can add a -d/--dry-run to any of the 3 examples above and it will show you the changes it **would** make.

## Personal Access Tokens (PAT)

You will need to [create a PAT](https://github.com/settings/tokens) with enough permissions to be able to update the repository labels.

<br />
<p align="right"><a href="https://wolfsoftware.com/"><img src="https://img.shields.io/badge/Created%20by%20Wolf%20on%20behalf%20of%20Wolf%20Software-blue?style=for-the-badge" /></a></p>
