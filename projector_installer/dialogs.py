#  GNU General Public License version 2
#
#  Copyright (C) 2019-2020 JetBrains s.r.o.
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 2 only, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import sys
import click
import netifaces
from .apps import get_installed_apps, get_app_path, get_compatible_app_names
from .run_config import get_run_configs, RunConfig, get_used_http_ports, get_used_projector_ports, get_run_config_names
from .global_config import DEF_HTTP_PORT, DEF_PROJECTOR_PORT


def display_run_configs_names(config_names):
    for i, config_name in enumerate(config_names):
        print(f'\t{i + 1:4}. {config_name}')


def list_configs(pattern=None):
    config_names = get_run_config_names(pattern)
    display_run_configs_names(config_names)


def display_run_configs(run_configs):
    config_names = list(run_configs.keys())
    config_names.sort()
    display_run_configs_names(config_names)


def find_apps(pattern=None):
    app_names = get_compatible_app_names(pattern)
    for i, app_name in enumerate(app_names):
        print(f'\t{i + 1:4}. {app_name}')


def list_apps(pattern=None):
    for i, app in enumerate(get_installed_apps(pattern)):
        print(f'\t{i + 1:4}. {app}')


def select_installed_app(pattern=None):
    apps = get_installed_apps(pattern)

    while True:
        list_apps(pattern)
        prompt = f"Choose an IDE number to uninstall or 0 to exit: [0-{len(apps)}]"
        app_number = click.prompt(prompt, type=int)

        if app_number < 0 or app_number > len(apps):
            print("Invalid number.")
            continue

        if app_number == 0:
            return None
        else:
            return apps[app_number - 1]


def select_known_app(pattern=None):
    app_names = get_compatible_app_names(pattern)

    while True:
        find_apps(pattern)
        prompt = f"Choose IDE number to install or 0 to exit: [0-{len(app_names)}]"
        app_number = click.prompt(prompt, type=int)

        if app_number < 0 or app_number > len(app_names):
            print("Invalid number.")
            continue

        if app_number == 0:
            return None
        else:
            return app_names[app_number - 1]


def select_unused_config_name(hint):
    run_configs = get_run_configs()
    cnt = 0
    res = hint

    while res in run_configs:
        cnt += 1
        res = f"{hint}_{cnt}"

    return res


def select_new_config_name(hint):
    run_config = get_run_configs()

    if hint:
        hint = select_unused_config_name(hint)
        prompt = "Enter a new configuration name or press ENTER for default"
    else:
        prompt = "Enter a new configuration name"

    while True:
        name = click.prompt(prompt, default=hint)

        if not name:
            return None

        if name in run_config:
            print(f"A configuration with name {name} already exists, please choose another name.")
            print("The known configurations:")
            list_configs()
            continue

        return name


def select_run_config(config_name):
    run_configs = get_run_configs(config_name)

    if len(run_configs) == 0:
        print(f'Configuration with name {config_name} is unknown, exiting...')
        sys.exit(1)

    if len(run_configs) > 1:
        while True:
            display_run_configs(run_configs)
            prompt = f"Choose a configuration number or 0 to exit: [0-{len(run_configs)}]"
            config_number = click.prompt(prompt, type=int)

            if config_number < 0 or config_number > len(run_configs):
                print("Invalid number selected.")
                continue

            if config_number == 0:
                print('Configuration was not selected, exiting...')
                sys.exit(1)
            else:
                config_names = get_run_config_names(config_name)
                name = config_names[config_number - 1]
                return name, run_configs[name]

    return list(run_configs.items())[0]


def select_installed_app_path():
    apps = get_installed_apps()

    while True:
        list_apps()
        prompt = f"Choose IDE number to install or 0 to exit: [0-{len(apps)}]"
        app_number = click.prompt(prompt, type=int)

        if app_number < 0 or app_number > len(apps):
            print("Invalid number selected.")
            continue

        if app_number == 0:
            return None
        else:
            return get_app_path(apps[app_number - 1])


def select_manual_app_path():
    path = click.prompt("Enter the path to IDE", type=str)
    return path


def select_app_path():
    apps = get_installed_apps()

    if apps:
        inst = click.prompt("Do you want to choose a Projector-installed IDE? [y/n]", type=bool)

        if inst:
            return select_installed_app_path()
        else:
            return select_manual_app_path()
    else:
        enter = click.prompt(
            "There are no installed Projector IDEs.\nWould you like to specify a path to IDE manually?",
            type=bool)
        if enter:
            return select_manual_app_path()
        else:
            return None

    return None


def get_def_port(ports, default):
    if len(ports) == 0:
        return default

    ports.sort()

    return ports[-1] + 1


def get_def_http_port():
    http_ports = get_used_http_ports()
    return get_def_port(http_ports, DEF_HTTP_PORT)


def get_def_projector_port():
    ports = get_used_projector_ports()
    return get_def_port(ports, DEF_PROJECTOR_PORT)


def get_local_addresses():
    interfaces = netifaces.interfaces()
    res = []

    for ifs in interfaces:
        addresses = netifaces.ifaddresses(ifs)

        if netifaces.AF_INET in addresses:
            ipv4 = addresses[netifaces.AF_INET]

            for ips in ipv4:
                res.append(ips['addr'])

    return res


def check_listening_address(address):
    if address == 'localhost':
        return True

    return address in get_local_addresses()


def select_http_address(default):
    while True:
        res = click.prompt("Enter HTTP listening address (press ENTER for default)", default=default)

        if check_listening_address(res):
            return res

        click.echo("You entered incorrect address, please try again.")


def select_http_port():
    port = get_def_http_port()
    return click.prompt("Enter a desired HTTP port (press ENTER for default)", default=port)


def select_projector_port():
    port = get_def_projector_port()
    return click.prompt("Enter a desired Projector port (press ENTER for default)", default=port)


def edit_config(config: RunConfig):
    prompt = "Enter the path to IDE (press ENTER for default)"
    config.path_to_app = click.prompt(prompt, default=config.path_to_app)

    prompt = "Enter a HTTP listening address (press ENTER for default)"
    config.http_address = click.prompt(prompt, default=config.http_address)

    prompt = "Enter a HTTP port (press ENTER for default)"
    config.http_port = click.prompt(prompt, default=config.http_port)

    prompt = "Enter a Projector port (press ENTER for default)"
    config.projector_port = click.prompt(prompt, default=config.projector_port)

    return config