#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: spywhere
# @Date:   2015-10-09 15:31:31
# @Last Modified by:   Sirisak Lueangsaksri
# @Last Modified time: 2015-10-09 16:53:03

import json
import os.path
import sys
import yaml


def load_json(json_file):
    return json.load(json_file)


def load_yaml(yaml_file):
    return yaml.load(yaml_file)


def save_json(json_data, json_file):
    json.dump(json_data, json_file, indent="  ", ensure_ascii=False)


def save_yaml(yaml_data, yaml_file):
    yaml.dump(
        yaml_data, yaml_file, allow_unicode=True, default_flow_style=False
    )


for input_path in sys.argv[1:]:
    input_dir = os.path.dirname(input_path)
    input_base_name = os.path.basename(input_path)
    file_name, input_file_ext = os.path.splitext(input_base_name)
    from_json = False
    if input_file_ext == ".json":
        from_json = True
        output_file_ext = ".yaml"
    else:
        output_file_ext = ".json"
    output_base_name = file_name + output_file_ext
    output_path = os.path.join(input_dir, output_base_name)

    print("Converting %s to %s... " % (
        input_base_name,
        output_base_name
    ), end='')
    input_file = open(input_path, "r", encoding="utf-8")
    if from_json:
        data = load_json(input_file)
    else:
        data = load_yaml(input_file)
    input_file.close()
    output_file = open(output_path, "w", encoding="utf-8")
    if from_json:
        save_yaml(data, output_file)
    else:
        save_json(data, output_file)
    output_file.close()
    print("done")
