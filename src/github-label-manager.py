#!/usr/bin/env python

"""
This script is designed to allow you to manage the labels on your GitHub repositories.

Keeping all your labels consistent makes it easier to work across multiple repositories (and organisations)

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
"""

import argparse
import json
import random
import re
import sys

from typing import Any, Literal

import colorama
import yaml

from github import Github, GithubException
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.PaginatedList import PaginatedList
from github.Repository import Repository

from yaspin import yaspin  # pylint: disable=import-error

# Initialize Colorama
colorama.init(autoreset=True)

# Constants
SUCCESS: str = colorama.Fore.GREEN
WARN: str = colorama.Fore.YELLOW
ERROR: str = colorama.Fore.RED
INFO: str = colorama.Fore.CYAN
BOLD: str = colorama.Style.BRIGHT
RESET: str = colorama.Style.RESET_ALL


def success(message: str) -> None:
    """
    Display a success messages to the user.

    Arguments:
        message (str): The message to display.
    """
    print(f'[ {BOLD}{SUCCESS}Success{RESET} ] {message}')


def warn(message: str) -> None:
    """
    Display a warning messages to the user.

    Arguments:
        message (str): The message to display.
    """
    print(f'[ {BOLD}{WARN}Warning{RESET} ] {message}')


def error(message: str) -> None:
    """
    Display an error messages to the user.

    Arguments:
        message (str): The message to display.
    """
    print(f'[ {BOLD}{ERROR}Error{RESET} ] {message}')


def info(message: str) -> None:
    """
    Display an informational messages to the user.

    Arguments:
        message (str): The message to display.
    """
    print(f'[ {BOLD}{INFO}Info{RESET} ] {message}')


def parser_error(message: str) -> None:
    """
    Display a parser error messages to the user.

    Arguments:
        message (str): The message to display.
    """
    print(f'github-label-manager: error: {message}')


def plural(number: int) -> Literal[''] | Literal['s']:
    """
    Pluralise a string based on a given number.

    Arguments:
        number (int): The number to pluralise.

    Returns:
        Literal[''] | Literal['s']: '' or s depending on the value of number.
    """
    return '' if number == 1 else 's'


def add_new_labels(client: Github, repo: str, labels_to_add: list, dry_run: bool) -> None:
    """
    Add new labels to the given repository.

    Arguments:
        client (Github): The authenticated github connection.
        repo (str): The name of the repository.
        labels_to_add (list): The list of labels to add.
        dry_run (bool): A flag to handle dry-runs.
    """
    print(f"Adding {len(labels_to_add)} new label{plural(len(labels_to_add))}")
    for label in labels_to_add:
        with yaspin(text=f"\tAdding '{label['name']}' ...", color="cyan") as spinner:
            if not dry_run:
                try:
                    client.get_repo(repo).create_label(name=label['name'], color=label['color'], description=label['description'])
                    spinner.ok("Done!")
                except GithubException as e:
                    spinner.fail(f"Failed! {e}")
                    error(f"Error creating label '{label['name']}': {e}")
            else:
                spinner.ok("Dry run!")


def delete_obsolete_labels(client: Github, repo: str, labels_to_delete: list, dry_run: bool) -> None:
    """
    Delete obsolete labels from the given repository.

    Arguments:
        client (Github): The authenticated github connection.
        repo (str): The name of the repository.
        labels_to_add (list): The list of labels to delete.
        dry_run (bool): A flag to handle dry-runs.
    """
    print(f"Deleting {len(labels_to_delete)} label{plural(len(labels_to_delete))}")
    for label in labels_to_delete:
        with yaspin(text=f"\tDeleting '{label['name']}' ...", color="cyan") as spinner:
            if not dry_run:
                try:
                    client.get_repo(repo).get_label(label['name']).delete()
                    spinner.ok("Done!")
                except GithubException as e:
                    spinner.fail(f"Failed! {e}")
                    error(f"Error deleting label '{label['name']}': {e}")
            else:
                spinner.ok("Dry run!")


def update_labels(client: Github, repo: str, labels_to_update: list, dry_run: bool) -> None:
    """
    Update existing labels on the given repository.

    Arguments:
        client (Github): The authenticated github connection.
        repo (str): The name of the repository.
        labels_to_add (list): The list of labels to update.
        dry_run (bool): A flag to handle dry-runs.
    """
    print(f"Updating {len(labels_to_update)} label{plural(len(labels_to_update))}")
    for label in labels_to_update:
        with yaspin(text=f"\tUpdating '{label['name']}' ...", color="cyan") as spinner:
            if not dry_run:
                try:
                    client.get_repo(repo).get_label(label['name']).edit(name=label['name'], color=label['color'], description=label['description'])
                    spinner.ok("Done!")
                except GithubException as e:
                    spinner.fail(f"Failed! {e}")
                    error(f"Error updating label '{label['name']}': {e}")
            else:
                spinner.ok("Dry run!")


def process_repo_labels(local_labels: list, repo_labels: list) -> tuple[list, list, list]:
    """
    Compare the local labels and the repository labels to work out what to add, delete and update.

    Arguments:
        local_labels (list): The local labels loaded from the config file.
        repo_labels (list): The labels extracted from the repository.

    Returns:
        tuple[list, list, list]: The list of labels to add, delete and update.
    """
    labels_to_update: list = []
    update_keys = set()

    local_diff: list = [label for label in local_labels if label not in repo_labels]
    remote_diff: list = [label for label in repo_labels if label not in local_labels]

    for local in local_diff:
        for remote in remote_diff:
            if local['name'].lower() == remote['name'].lower():
                labels_to_update.append(local)
                update_keys.add(local['name'].lower())

    labels_to_add: list = [label for label in local_diff if label['name'].lower() not in update_keys]
    labels_to_delete: list = [label for label in remote_diff if label['name'].lower() not in update_keys]

    return labels_to_add, labels_to_delete, labels_to_update


def get_repo_labels(client: Github, repo: str) -> list[dict[str, Any]] | list:
    """
    Extract the list of labels currently used by a given repository.

    Arguments:
        client (Github): The authenticated github connection.
        repo (str): The name of the repository.

    Returns:
        list[dict[str, Any]] | list: The labels extracted from the repository.
    """
    try:
        labels: Any = client.get_repo(repo).get_labels()
        return [
            {'name': label.name, 'color': label.color.upper(), 'description': label.description}
            for label in labels
        ]
    except GithubException as err:
        error(f"Failed to retrieve labels from {repo}: {err}")
        return []


def process_labels(client: Github, repo: str, local_labels: list, dry_run: bool) -> None:
    """
    Process the labels for a given repository.

    This includes extracting the labels from the repository, calculating what to add, delete and
    update and performing the additions, deletions and updates.

    Arguments:
        client (Github): The authenticated github connection.
        repo (str): The name of the repository.
        labels_to_add (list): The list of labels to update.
        dry_run (bool): A flag to handle dry-runs.
    """
    labels_to_add: list = []
    labels_to_delete: list = []
    labels_to_update: list = []

    try:
        info(f"Processing Labels for {repo}:")
        repo_labels: list[dict[str, Any]] | list = get_repo_labels(client, repo)

        labels_to_add, labels_to_delete, labels_to_update = process_repo_labels(local_labels, repo_labels)

        add_new_labels(client, repo, labels_to_add, dry_run)
        delete_obsolete_labels(client, repo, labels_to_delete, dry_run)
        update_labels(client, repo, labels_to_update, dry_run)
    except GithubException as err:
        error(f"Error processing labels for {repo}: {err}")


def validate_local_labels(labels: list) -> None:
    """
    Validate the labels in the config file.

    Arguments:
        labels (list): The local labels loaded from the config file.
    """
    info(f"Validating {len(labels)} Labels")
    for label in labels:
        print(f"Validating label '{label['name']}'")
        if re.match(r"^[A-F0-9]{3,6}$", label['color'], re.IGNORECASE):
            success(f"\tColor '{label['color']}' is valid")
        else:
            error(f"\tColor '{label['color']}' is invalid")

        if label['description'] is None or len(label['description']) <= 100:
            success("\tDescription is valid")
        elif len(label['description']) > 100:
            error(f"\tDescription is too long {len(label['description'])} characters (max 100)")
        else:
            error("\tDescription is invalid")


def generate_random_color() -> str:
    """
    Generate a random HTML valid hex color code using f-string for formatting.

    Returns:
        str: A string representing a valid hex color code.
    """
    # Generate a random integer between 0 and 0xFFFFFF (inclusive)
    # and format it as a hexadecimal string using f-string formatting.
    return f"#{random.randint(0, 0xFFFFFF):06x}"  # nosec B311


def load_labels_from_json_file(filename: str) -> list:
    """
    Load labels from a JSON file and normalize their properties.

    This function reads a list of labels from a specified JSON file.

    Arguments:
        filename (str): Path to the JSON file containing label data.

    Returns:
        list: A list of label dictionaries with normalized properties.
    """
    try:
        with open(filename, 'r', encoding='UTF-8') as file:
            labels: Any = json.load(file)
        return labels
    except json.JSONDecodeError:
        print("Parse Error in JSON file.")
        sys.exit(1)
    except IOError:
        print("File not found or inaccessible.")
        sys.exit(1)


def load_labels_from_yaml_file(filename: str) -> list:
    """
    Load labels from a YAML file and normalize their properties.

    This function reads a list of labels from a specified YAML file and converts the result into JSON.

    Arguments:
        filename (str): Path to the JSON file containing label data.

    Returns:
        list: A list of label dictionaries with normalized properties.
    """
    try:
        with open(filename, 'r', encoding='UTF-8') as file:
            yaml_data: Any = yaml.safe_load(file)
            json_str: str = json.dumps(yaml_data)
        return json.loads(json_str)
    except yaml.YAMLError:
        print("Parse Error in YAML file.")
        sys.exit(1)
    except IOError:
        print("File not found or inaccessible.")
        sys.exit(1)


def load_labels_from_file(filename: str, args: argparse.Namespace) -> list:
    """
    Load labels from a specified file and normalize their properties.

    This function reads a list of labels from a specified file. It removes any labels without a 'name',
    sets 'description' to an empty string if it's missing or None, and assigns a random color if 'color' is missing.

    Arguments:
        filename (str): Path to the file containing label data.

    Returns:
        list: A list of label dictionaries with normalized properties.
    """
    if args.json:
        labels: list = load_labels_from_json_file(filename)
    else:
        labels = load_labels_from_yaml_file(filename)

    # Process labels, filtering out invalid entries and normalizing data
    valid_labels: list = []

    for label in labels:
        if 'name' not in label or not label['name']:
            print("Warning: A label without a valid name was found and removed.")
            continue
        label['description'] = '' if 'description' not in label or label['description'] is None else label['description']
        label['color'] = generate_random_color() if 'color' not in label or not label['color'] else label['color']
        valid_labels.append(label)

    # Sort labels by name
    valid_labels.sort(key=lambda label: label['name'].lower())
    return valid_labels


def setup_client(token: str) -> Github:
    """
    Create a new Github client using the token for authentication.

    Arguments:
        token (str): The Github PAT to use for authentication.

    Returns:
        Github: The authenticated github connection.
    """
    try:
        client = Github(token)
        return client
    except GithubException:
        print("Invalid token")
        sys.exit()


def update_selected_repos(args: argparse.Namespace, local_labels: list) -> None:
    """
    Calculate which repos to update based on the command line arguments supplied.

    Arguments:
        args (argparse.Namespace): The command line arguments.
        local_labels (list): THe list of labels loaded from the config file.
    """
    client: Github = setup_client(args.token)

    if args.user:
        try:
            user: NamedUser | AuthenticatedUser = client.get_user(args.user)
            user_repos: PaginatedList[Repository] = user.get_repos(sort='full_name')

            for repo in user_repos:
                process_labels(client, repo.full_name, local_labels, args.dry_run)
        except GithubException as err:
            error(f"Failed to process user {user.login}: {err}")
    elif args.repo:
        process_labels(client, args.repo, local_labels, args.dry_run)
    elif args.org:
        try:
            org: Organization = client.get_organization(args.org)
            org_repos: PaginatedList[Repository] = org.get_repos(sort='full_name')
            for repo in org_repos:
                process_labels(client, repo.full_name, local_labels, args.dry_run)
        except GithubException as err:
            error(f"Failed to process organization {args.org}: {err}")
    else:
        error("Invalid repository or organization specified.")


def setup_arg_parser() -> argparse.ArgumentParser:
    """
    Configure the argument parser.

    Returns:
        argparse.ArgumentParser: The arguments parser.
    """
    parser = argparse.ArgumentParser(prog="github-label-manager",
                                     description="Setup labels on git repository.",
                                     add_help=False,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    flags: argparse._ArgumentGroup = parser.add_argument_group('flags')
    flags_mex: argparse._ArgumentGroup = parser.add_argument_group('mutually exclusive flags')
    flags_mex_group: argparse._MutuallyExclusiveGroup = flags_mex.add_mutually_exclusive_group()
    selective: argparse._ArgumentGroup = parser.add_argument_group('selective')
    required: argparse._ArgumentGroup = parser.add_argument_group('required')
    required_mex: argparse._ArgumentGroup = parser.add_argument_group('mutually exclusive')
    required_mex_group: argparse._MutuallyExclusiveGroup = required_mex.add_mutually_exclusive_group()

    # Command line flags
    flags.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="show this help message and exit.")
    flags.add_argument('-d', '--dry-run', action='store_true', help='Perform a dry run')
    flags.add_argument('-v', '--validate', action='store_true', help='Validate local labels')

    # Mutually exclusive flags
    flags_mex_group.add_argument('-j', '--json', action='store_true', default=True, help='JSON formatted config file')
    flags_mex_group.add_argument('-y', '--yaml', action='store_true', help='YAML formatted config file')

    # Optional arguments
    selective.add_argument('-t', '--token', type=str, help='GitHub token (needed for everything except -v/--validate)')

    # Required arguments
    required.add_argument('-f', '--filename', type=str, required=True, help='File containing labels')

    required_mex_group.add_argument('-u', '--user', type=str, help='Specify username')
    required_mex_group.add_argument('-o', '--org', type=str, help='Specify organization')
    required_mex_group.add_argument('-r', '--repo', type=str, help='Specify repository')

    return parser


def process_arguments() -> None:
    """
    Process the command line arguments.

    Setup the arguments parser, parser the arguments, validate the input and then action the requested changed.
    """
    parser: argparse.ArgumentParser = setup_arg_parser()
    args: argparse.Namespace = parser.parse_args()

    if args.yaml:
        args.json = False

    local_labels: Any = load_labels_from_file(args.filename, args)

    if args.validate:
        validate_local_labels(local_labels)
        sys.exit(0)

    if not args.repo and not args.org and not args.user:
        parser_error("one of the arguments -u/--user -o/--org -r/--repo is required")
        sys.exit(0)

    if not args.token:
        parser_error("the following arguments are required: -t/--token")
        sys.exit(1)

    update_selected_repos(args, local_labels)


def main() -> None:
    """
    Execute the main routine of the script.

    This function serves as the entry point of the script. It is responsible
    for invoking the `process_arguments` function, which handles the processing
    of command-line arguments. The `main` function does not take any parameters
    and does not return any value. It ensures that the script's functionality
    is triggered correctly when the script is executed.
    """
    process_arguments()


if __name__ == "__main__":
    main()
