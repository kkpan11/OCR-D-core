"""
Operating system functions.
"""
__all__ = [
    'abspath',
    'directory_size',
    'is_file_in_directory',
    'get_ocrd_tool_json',
    'get_moduledir',
    'get_processor_resource_types',
    'guess_media_type',
    'pushd_popd',
    'unzip_file_to_dir',
    'atomic_write',
    'redirect_stderr_and_stdout_to_file',
]

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from tempfile import TemporaryDirectory, gettempdir
from functools import lru_cache
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from shutil import which
from json import loads
from json.decoder import JSONDecodeError
from os import getcwd, chdir, stat, chmod, umask, environ, PathLike
from pathlib import Path
from os.path import abspath as abspath_, join
from zipfile import ZipFile
from subprocess import run, PIPE
from mimetypes import guess_type as mimetypes_guess
from filetype import guess as filetype_guess

from atomicwrites import atomic_write as atomic_write_, AtomicWriter

from .constants import EXT_TO_MIME, RESOURCE_LOCATIONS, RESOURCES_DIR_SYSTEM
from .config import config
from .logging import getLogger
from .introspect import resource_string

def abspath(url : str) -> str:
    """
    Get a full path to a file or file URL

    See os.abspath
    """
    if url.startswith('file://'):
        url = url[len('file://'):]
    return abspath_(url)

@contextmanager
def pushd_popd(newcwd : Union[str, PathLike] = None, tempdir : bool = False) -> Iterator[PathLike]:
    if newcwd and tempdir:
        raise Exception("pushd_popd can accept either newcwd or tempdir, not both")
    try:
        oldcwd = getcwd()
    except FileNotFoundError:
        # This happens when a directory is deleted before the context is exited
        oldcwd = gettempdir()
    try:
        if tempdir:
            with TemporaryDirectory() as tempcwd:
                chdir(tempcwd)
                yield Path(tempcwd).resolve()
        else:
            if newcwd:
                chdir(newcwd)
            yield Path(newcwd).resolve()
    finally:
        chdir(oldcwd)

def unzip_file_to_dir(path_to_zip : Union[str, PathLike], output_directory : str) -> None:
    """
    Extract a ZIP archive to a directory
    """
    with ZipFile(path_to_zip, 'r') as z:
        z.extractall(output_directory)

@lru_cache()
def get_ocrd_tool_json(executable : str) -> Dict[str, Any]:
    """
    Get the ``ocrd-tool`` description of ``executable``.
    """
    ocrd_tool = {}
    executable_name = Path(executable).name
    try:
        ocrd_all_tool = loads(resource_string('ocrd', 'ocrd-all-tool.json'))
        ocrd_tool = ocrd_all_tool[executable]
    except (JSONDecodeError, OSError, KeyError):
        try:
            ocrd_tool = loads(run([executable, '--dump-json'], stdout=PIPE, check=False).stdout)
        except (JSONDecodeError, OSError) as e:
            getLogger('ocrd.utils.get_ocrd_tool_json').error(f'{executable} --dump-json produced invalid JSON: {e}')
    if 'resource_locations' not in ocrd_tool:
        ocrd_tool['resource_locations'] = RESOURCE_LOCATIONS
    return ocrd_tool

@lru_cache()
def get_moduledir(executable : str) -> str:
    moduledir = None
    try:
        ocrd_all_moduledir = loads(resource_string('ocrd', 'ocrd-all-module-dir.json'))
        moduledir = ocrd_all_moduledir[executable]
    except (JSONDecodeError, OSError, KeyError):
        try:
            moduledir = run([executable, '--dump-module-dir'], encoding='utf-8', stdout=PIPE, check=False).stdout.rstrip('\n')
        except (JSONDecodeError, OSError) as e:
            getLogger('ocrd.utils.get_moduledir').error(f'{executable} --dump-module-dir failed: {e}')
    return moduledir

def list_resource_candidates(executable : str, fname : str, cwd : Optional[str] = None, moduled : Optional[str] = None, xdg_data_home : Optional[str] = None) -> List[str]:
    """
    Generate candidates for processor resources according to
    https://ocr-d.de/en/spec/ocrd_tool#file-parameters
    """
    if cwd is None:
        cwd = getcwd()
    candidates = []
    candidates.append(join(cwd, fname))
    xdg_data_home = xdg_data_home or config.XDG_DATA_HOME
    processor_path_var = '%s_PATH' % executable.replace('-', '_').upper()
    if processor_path_var in environ:
        candidates += [join(x, fname) for x in environ[processor_path_var].split(':')]
    candidates.append(join(xdg_data_home, 'ocrd-resources', executable, fname))
    candidates.append(join(RESOURCES_DIR_SYSTEM, executable, fname))
    if moduled:
        candidates.append(join(moduled, fname))
    return candidates

def list_all_resources(executable : str, moduled : Optional[str] = None, xdg_data_home : Optional[str] = None) -> List[Tuple[str,str]]:
    """
    List all processor resources in the filesystem according to
    https://ocr-d.de/en/spec/ocrd_tool#file-parameters
    """
    candidates = []
    try:
        resource_locations = get_ocrd_tool_json(executable)['resource_locations']
    except FileNotFoundError:
        # processor we're looking for resource_locations of is not installed.
        # Assume the default
        resource_locations = RESOURCE_LOCATIONS
    xdg_data_home = xdg_data_home or config.XDG_DATA_HOME
    # we need both the full path and its base location directory
    # so we can subtract the latter from the former as resource name
    def iterbase(base):
        for subpath in base.iterdir():
            yield (base, subpath)
    # XXX cwd would list too many false positives
    # if 'cwd' in resource_locations:
    #     cwd_candidate = join(getcwd(), 'ocrd-resources', executable)
    #     if Path(cwd_candidate).exists():
    #         candidates.append(cwd_candidate)
    processor_path_var = '%s_PATH' % executable.replace('-', '_').upper()
    if processor_path_var in environ:
        for processor_path in environ[processor_path_var].split(':'):
            processor_path = Path(processor_path)
            if processor_path.is_dir():
                candidates += iterbase(processor_path)
    if 'data' in resource_locations:
        datadir = Path(xdg_data_home, 'ocrd-resources', executable)
        if datadir.is_dir():
            candidates += iterbase(datadir)
    if 'system' in resource_locations:
        systemdir = Path(RESOURCES_DIR_SYSTEM, executable)
        if systemdir.is_dir():
            candidates += iterbase(systemdir)
    if 'module' in resource_locations and moduled:
        # recurse fully
        base = Path(moduled)
        for resource in itertree(base):
            if resource.is_dir():
                continue
            if any(resource.match(pattern) for pattern in
                   # Python distributions do not distinguish between
                   # code and data; `is_resource()` only singles out
                   # files over directories; but we want data files only
                   # todo: more code and cache exclusion patterns!
                   ['*.py', '*.py[cod]', '*~', '.*.swp', '*.swo',
                    '__pycache__/*', '*.egg-info/*', '*.egg',
                    'copyright.txt', 'LICENSE*', 'README.md', 'MANIFEST',
                    'TAGS', '.DS_Store',
                    # C extensions
                    '*.so',
                    # translations
                    '*.mo', '*.pot',
                    '*.log', '*.orig', '*.BAK',
                    '.git/*',
                    # our stuff
                    'ocrd-tool.json',
                    'environment.pickle', 'resource_list.yml', 'lib.bash']):
                continue
            candidates.append((base, resource))
    return sorted([(str(base), str(path))
                   for base, path in candidates
                   if path.name not in ['.git']])

def get_processor_resource_types(executable : str, ocrd_tool : Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Determine what type of resource parameters a processor needs.

    Return a list of MIME types (with the special value `*/*` to
    designate that arbitrary files or directories are allowed).
    """
    if not ocrd_tool:
        # if the processor in question is not installed, assume both files and directories
        if not which(executable):
            return ['*/*']
        ocrd_tool = get_ocrd_tool_json(executable)
    mime_types = [mime
                  for param in ocrd_tool['parameters'].values()
                  if param['type'] == 'string' and param.get('format', '') == 'uri' and 'content-type' in param
                  for mime in param['content-type'].split(',')]
    if not len(mime_types):
        # None of the parameters for this processor are resources
        # (or the parameters' resource types are not properly declared,)
        # so output both directories and files
        return ['*/*']
    return mime_types

# ht @pabs3
# https://github.com/untitaker/python-atomicwrites/issues/42
class AtomicWriterPerms(AtomicWriter):
    def get_fileobject(self, **kwargs):
        f = super().get_fileobject(**kwargs)
        try:
            mode = stat(self._path).st_mode
        except FileNotFoundError:
            # Creating a new file, emulate what os.open() does
            mask = umask(0)
            umask(mask)
            mode = 0o664 & ~mask
        fd = f.fileno()
        chmod(fd, mode)
        return f

@contextmanager
def atomic_write(fpath : str) -> Iterator[str]:
    with atomic_write_(fpath, writer_cls=AtomicWriterPerms, overwrite=True) as f:
        yield f


def is_file_in_directory(directory : Union[str, PathLike], file : Union[str, PathLike]) -> bool:
    """
    Return True if ``file`` is in ``directory`` (by checking that all components of ``directory`` are in ``file.parts``)
    """
    directory = Path(directory)
    file = Path(file)
    return list(file.parts)[:len(directory.parts)] == list(directory.parts)

def itertree(path : Union[str, PathLike]) -> PathLike:
    """
    Generate a list of paths by recursively enumerating ``path``
    """
    if not isinstance(path, Path):
        path = Path(path)
    if path.is_dir():
        for subpath in path.iterdir():
            yield from itertree(subpath)
    yield path

def directory_size(path : Union[str, PathLike]) -> int:
    """
    Calculates size of all files in directory ``path``
    """
    path = Path(path)
    return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

def guess_media_type(input_file : str, fallback : Optional[str] = None, application_xml : str = 'application/xml') -> str:
    """
    Guess the media type of a file path
    """
    mimetype = filetype_guess(input_file)
    if mimetype is not None:
        mimetype = mimetype.mime
    else:
        mimetype = mimetypes_guess(input_file)[0]
    if mimetype is None:
        mimetype = EXT_TO_MIME.get(''.join(Path(input_file).suffixes), fallback)
    if mimetype is None:
        raise ValueError("Could not determine MIME type of input_file '%s'", str(input_file))
    if mimetype == 'application/xml':
        mimetype = application_xml
    return mimetype

@contextmanager
def redirect_stderr_and_stdout_to_file(filename):
    with open(filename, 'at', encoding='utf-8') as f:
        with redirect_stderr(f), redirect_stdout(f):
            yield
