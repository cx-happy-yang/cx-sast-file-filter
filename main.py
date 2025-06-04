import os
from pathlib import Path
from argparse import (
    ArgumentParser,
)

import logging

# create logger
logger = logging.getLogger("cx-sast-filter-filter")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
time_stamp_format = "%Y-%m-%dT%H:%M:%S.%fZ"

__all__ = ["logger"]


def get_cx_supported_file_extensions():
    return ['.ac', '.am', '.apexp', '.app', '.apxc', '.asax', '.ascx', '.asp', '.aspx', '.bas', '.c', '.c++', '.cbl',
            '.cc', '.cfg', '.cgi', '.cls', '.cmake', '.cmp', '.cob', '.component', '.conf', '.config',
            '.configurations', '.cpp', '.cpy', '.cs', '.cshtml', '.csproj', '.csv', '.ctl', '.ctp', '.cxx', '.dart',
            '.dspf', '.dsr', '.ec', '.eco', '.env', '.env_cxsca-container-build-args', '.erb', '.evt', '.frm', '.ftl',
            '.go', '.gradle', '.groovy', '.gsh', '.gsp', '.gtl', '.gvy', '.gy', '.h', '.h++', '.handlebars', '.hbs',
            '.hh', '.hpp', '.htm', '.html', '.hxx', '.inc', '.ini', '.jade', '.java', '.js', '.jsf', '.json', '.jsp',
            '.jspdsbld', '.jspf', '.jsx', '.kt', '.kts', '.latex', '.lock', '.lua', '.m', '.master', '.mf', '.mod',
            '.mustache', '.npmrc', '.object', '.page', '.pc', '.pck', '.pco', '.ph', '.php', '.php3', '.php4', '.php5',
            '.phtm', '.phtml', '.pkb', '.pkh', '.pks', '.pl', '.plist', '.pls', '.plx', '.pm', '.private', '.pro',
            '.properties', '.psgi', '.pug', '.py', '.rb', '.report', '.resolved', '.rev', '.rhtml', '.rjs', '.rpg',
            '.rpg38',
            '.rpgle', '.rs', '.rxml',  '.sbt', '.scala', '.snapshot', '.sqb', '.sql', '.sqlrpg', '.sqlrpgle', '.sum',
            '.swift', '.tag', '.target', '.testtarget', '.tex', '.tgr', '.tld', '.toml', '.tpl', '.trigger', '.ts',
            '.tsx', '.twig', '.txt', '.vb', '.vbp', '.vbproj', '.vbs', '.vm', '.vue', '.wod', '.workflow', '.xaml',
            '.xhtml', '.xib', '.xml', '.xsaccess', '.xsapp', '.xsjs', '.xsjslib', '.yaml', '.yarnrc', '.yml']


def get_cx_supported_file_without_extensions():
    return ["dockerfile", "cartfile", "podfile", "gemfile", "cpanfile", "exclude", "head", "master", "main",
            "commit_editmsg", "config", "description", "index", "packed-refs"]


def group_str_by_wildcard_character(exclusions):
    """

    Args:
        exclusions (str): comma separated string
        for example, "*.min.js,readme,*.txt,test*,*doc*"

    Returns:
        dict
        {
         "prefix_list": ["test"], # wildcard (*) at end, but not start
         "suffix_list": [".min.js", ".txt"],  # wildcard (*) at start, but not end
         "inner_List": ["doc"],   # wildcard (*) at both end and start
         "word_list": ["readme"]  # no wildcard
        }
    """
    result = {
        "prefix_list": [],
        "suffix_list": [],
        "inner_List": [],
        "word_list": [],
    }
    if not exclusions:
        return result
    string_list = exclusions.lower().split(',')
    string_set = set(string_list)
    for string in string_set:
        new_string = string.strip()
        # ignore any string that with slash or backward slash
        if '/' in new_string or "\\" in new_string:
            continue
        if new_string.endswith("*") and not new_string.startswith("*"):
            result["prefix_list"].append(new_string.rstrip("*"))
        elif new_string.startswith("*") and not new_string.endswith("*"):
            result["suffix_list"].append(new_string.lstrip("*"))
        elif new_string.endswith("*") and new_string.startswith("*"):
            result["inner_List"].append(new_string.strip("*"))
        else:
            result["word_list"].append(new_string)
    return result


def should_be_excluded(exclusions, target):
    """

    Args:
        exclusions (str):
        target (str):

    Returns:

    """
    result = False
    target = target.lower()
    groups_of_exclusions = group_str_by_wildcard_character(exclusions)
    if target.startswith(tuple(groups_of_exclusions["prefix_list"])):
        result = True
    if target.endswith(tuple(groups_of_exclusions["suffix_list"])):
        result = True
    if any([True if inner_text in target else False for inner_text in groups_of_exclusions["inner_List"]]):
        result = True
    if target in groups_of_exclusions["word_list"]:
        result = True
    return result


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    description = 'A simple command-line interface for CxSAST in Python.'
    parser = ArgumentParser(description=description)
    parser.add_argument('--exclude_folders', required=False, help="exclude folders, comma separated string")
    parser.add_argument('--exclude_files', required=False, help="exclude files, comma separated string")
    parser.add_argument('--sources_directory', required=False, help="The local path on the agent where "
                                                                    "your source code files are downloaded ")
    arguments = parser.parse_known_args()[0]
    exclude_folders = arguments.exclude_folders or ""
    exclude_files = arguments.exclude_files or ""
    sources_directory = arguments.sources_directory
    logger.info(
        f"arguments from command line:"
        f"exclude_folders: {exclude_folders}\n"
        f"exclude_files: {exclude_files}\n"
        f"sources_directory: {sources_directory}\n"
    )
    if not sources_directory:
        logger.info("sources_directory not defined from CLI")
        sources_directory = os.getenv("Build.SourcesDirectory")
        logger.info(f"sources_directory read from environment variable Build.SourcesDirectory: {sources_directory}")
    exclude_folders += ",.*,bin,target,images,Lib,node_modules"
    exclude_files += ",*.min.js"

    extensions = get_cx_supported_file_extensions()
    file_without_extensions = get_cx_supported_file_without_extensions()
    path = Path(sources_directory)
    if not path.exists():
        logger.error(f"{sources_directory} does not exist")
        exit()
    absolute_path_str = str(os.path.normpath(path.absolute()))

    for base, dirs, files in os.walk(absolute_path_str):
        path_folders = base.split(os.sep)
        evaluate_dot_git_folder = True
        if any([should_be_excluded(exclude_folders, folder) for folder in path_folders]):
            continue
        for file in files:
            file_name = file.lower()
            file_path = Path(os.path.join(base, file))
            try:
                if "." not in file_name and file_name not in file_without_extensions:
                    logger.info(f"Remove file {file_path}")
                    if file_path.exists():
                        os.remove(file_path)
                if "." in file_name and not file_name.endswith(tuple(extensions)):
                    logger.info(f"Remove file {file_path}")
                    if file_path.exists():
                        os.remove(file_path)
                if should_be_excluded(exclude_files, file_name):
                    logger.info(f"Remove file {file_path}")
                    if file_path.exists():
                        os.remove(file_path)
            except PermissionError:
                logger.info(f"Fail to remove file {file_path} as denied")
                continue
