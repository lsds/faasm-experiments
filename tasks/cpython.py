from os.path import join
from subprocess import run
from copy import copy
import os

from invoke import task

from multiprocessing import cpu_count

from faasmcli.util.files import clean_dir
from tasks.util.env import EXPERIMENTS_THIRD_PARTY
from faasmcli.util.toolchain import (
    BASE_CONFIG_CMD,
    WASM_CFLAGS,
    WASM_HOST,
    WASM_BUILD,
    WASM_LDFLAGS,    
)

CPYTHON_DIR = join(EXPERIMENTS_THIRD_PARTY, "cpython")

# See the CPython docs for more info:
# - General: https://devguide.python.org/setup/#compile-and-build
# - Static builds: https://wiki.python.org/moin/BuildStatically


@task
def lib(ctx, clean=False):
    work_dir = join(CPYTHON_DIR)
    build_dir = join(work_dir, "build", "wasm")
    install_dir = join(work_dir, "install", "wasm")

    clean_dir(build_dir, clean)
    clean_dir(install_dir, clean)
    if clean:
        run("make clean", shell=True, cwd=work_dir)

    env_vars = copy(os.environ)       

    configure_cmd = ["./configure"]
    configure_cmd.extend(BASE_CONFIG_CMD)
    configure_cmd.extend([
        "--with-pydebug",
        "--disable-ipv6",
        "--without-pymalloc",
        "--disable-shared",
        "--build={}".format(WASM_BUILD),
        "--host={}".format(WASM_HOST),
        "--prefix={}".format(install_dir)
        ])

    cflags = [
            WASM_CFLAGS,
            ]
    cflags = " ".join(cflags)

    ldflags = [
            WASM_LDFLAGS,
            "-static",
            ]
    ldflags = " ".join(ldflags)

    configure_cmd.extend([
        'CFLAGS="{}"'.format(cflags),
        'CPPFLAGS="{}"'.format(cflags),
        'LDFLAGS="{}"'.format(ldflags),
    ])

    configure_str = " ".join(configure_cmd)
    print(configure_str)

    print("RUNNING CONFIGURE")
    res = run(configure_str, shell=True, cwd=work_dir, env=env_vars)
    if res.returncode != 0:
        raise RuntimeError("CPython configure failed ({})".format(
            res.returncode
            ))

    cpus = int(cpu_count()) - 1
    make_cmd = [
        "make -j {}".format(cpus),
        'LDFLAGS="-static"',
        'LINKFORSHARED=" "',
    ]
    make_cmd = " ".join(make_cmd)

    res = run(make_cmd, shell=True, cwd=work_dir)
    if res.returncode != 0:
        raise RuntimeError("CPython make failed ({})".format(res.returncode))

