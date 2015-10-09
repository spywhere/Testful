#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: spywhere
# @Date:   2015-10-02 09:54:10
# @Last Modified by:   Sirisak Lueangsaksri
# @Last Modified time: 2015-10-09 16:52:38

import json
import os
import re
import sys
import time
import urllib.request
import yaml

FLAGS = {
    "verbose": False,
    "yaml": False
}
INPUT_MAP = {}
SPECIAL_MACROS = ["datetime"]
MACROS = {}
MACRO_PATTERN = re.compile("<%(\\w+)(:(.*[^%>]))?%>")
DATA_PATTERN = re.compile("<<([\\w-]+(\\.[\\w-]+)*)>>")
TEST_SUITE_FILE_NAME = "test_config.yaml"
TEST_RESULT_FILE_NAME = "results.testful"


def load_data(raw_data):
    return yaml.load(raw_data)


def represent_data(data):
    if FLAGS["yaml"]:
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
    else:
        return json.dumps(data, indent="  ", ensure_ascii=False)


def save_data(data, out_file=None):
    if out_file:
        return yaml.dump(data, out_file, allow_unicode=True, default_flow_style=False)
    else:
        return yaml.dump(data, allow_unicode=True)


def from_json(raw_data):
    return json.loads(raw_data)


def to_json(data):
    return json.dumps(data)


def is_expected_data(actual, expect, critical=True, path=None):
    path = path or []
    if type(actual) != type(expect):
        return "Expected \"%s\"%s but got \"%s\" instead" % (
            expect,
            " in the \"%s\"" % (".".join(path)) if path else "",
            actual
        )

    if (isinstance(expect, dict) or isinstance(expect, list) or
            isinstance(expect, tuple)):
        for ex_key in expect:
            ex_key_or_value = ex_key
            if not isinstance(expect, dict):
                ex_key = expect.index(ex_key_or_value)
            ex_val = expect[ex_key]
            if isinstance(expect, dict):
                if ex_key not in actual:
                    return "Expected \"%s\" in the %s" % (
                        ex_key,
                        "\"%s\"" % (".".join(path)) if path else "actual dict"
                    )
            else:
                return is_expected_data(
                    actual[ex_key],
                    ex_val,
                    critical,
                    path + [str(ex_key)]
                )
            if (isinstance(ex_val, dict) or isinstance(ex_val, list) or
                    isinstance(ex_val, tuple)):
                return is_expected_data(
                    actual[ex_key],
                    expect[ex_key],
                    critical,
                    path + [str(ex_key)]
                )
            assert_error = is_expected_data(
                actual[ex_key],
                ex_val,
                critical,
                path + [str(ex_key)]
            )
            if assert_error:
                return assert_error
        return None
    else:
        if actual == expect:
            return None
        else:
            return "Expected \"%s\"%s but got \"%s\" instead" % (
                expect,
                " in the \"%s\"" % (".".join(path)) if path else "",
                actual
            )


def gather_special_macro(name, format):
    if name == "datetime":
        if format:
            return time.strftime(format)
        else:
            return str(int(time.time()))
    return ""


def gather_macro(key, type=None):
    global INPUT_LINES, MACROS
    if key in MACROS:
        return MACROS[key]
    if key in SPECIAL_MACROS:
        return gather_special_macro(key, type)
    if key in INPUT_MAP:
        value = str(INPUT_MAP[key])
        print("%s: %s" % (key, value))
    else:
        value = input(key + ": ")
    MACROS[key] = value
    return value


def process_macro(body):
    data = save_data(body)
    data = MACRO_PATTERN.sub(
        lambda m: gather_macro(m.group(1), m.group(3)),
        data
    )
    return load_data(data)


def gather_data(data, key, root=True):
    keys = key.split(".")
    if not keys:
        return str(data)
    if isinstance(data, list) or isinstance(data, tuple):
        try:
            index = int(keys[0])
        except:
            if not root:
                print("Warning! Missing value for key \"%s\"" % (keys[0]))
            return ""
        if len(data) <= index:
            print("Warning! Missing key \"%s\"" % (keys[0]))
            return ""
        return gather_data(data[index], ".".join(keys[1:]), False)
    elif isinstance(data, dict):
        if not root and keys[0] not in data:
            print("Warning! Missing key \"%s\"" % (keys[0]))
            return ""
        elif root and keys[0] not in data and len(data) == 1:
            data = list(data.values())[0]
        elif root and keys[0] in data:
            return gather_data(data[keys[0]], ".".join(keys[1:]), True)
        return gather_data(data[keys[0]], ".".join(keys[1:]), False)
    else:
        return str(data)


def process_raw_data(body, data):
    return DATA_PATTERN.sub(
        lambda m: gather_data(data, m.group(1)),
        body
    )


def process_body_data(body, data):
    data_obj = save_data(body)
    return load_data(process_raw_data(data_obj, data))


def run_test(test_suite, namespace, result_file=None, critical=True,
             parent=None, aux=None):
    parent = parent or {}
    parent_response = {}
    if "parent_response" in parent:
        parent_response = parent["parent_response"]
    host = ""
    verbose = "verbose" in test_suite and test_suite["verbose"]
    if "host" in parent:
        host = parent["host"]
    if "host" in test_suite:
        host = process_raw_data(test_suite["host"], parent_response)
    test_suite["host"] = host
    path = ""
    if "path" in parent:
        path = parent["path"]
    if "path" in test_suite:
        path = process_raw_data(test_suite["path"], parent_response)
    test_suite["path"] = path
    name = ""
    if "name" in parent:
        name += parent["name"]
    if "name" in test_suite:
        if name != "":
            name += "-"
        name += process_raw_data(test_suite["name"], parent_response)
    identifier = name
    if "identifier" in test_suite:
        identifier = test_suite["identifier"]
    test_suite["name"] = name
    get_body = {}
    post_body = None
    expected_json = {}
    if "setup" in test_suite:
        setup_status = run_test(
            test_suite["setup"],
            namespace,
            result_file,
            False,
            parent,
            "setup"
        )
        if not setup_status:
            return False
    if "get" in test_suite:
        get_body = process_body_data(
            test_suite["get"],
            parent_response
        )
        if FLAGS["verbose"] or verbose:
            print(("=" * 10) + " GET " + ("=" * 10))
            print(represent_data(get_body))
            print("-" * 25)
    if "post" in test_suite:
        post_body = process_body_data(
            test_suite["post"],
            parent_response
        )
        if FLAGS["verbose"] or verbose:
            print(("=" * 10) + " POST " + ("=" * 10))
            print(represent_data(post_body))
            print("-" * 26)

    if "expected_json" in test_suite:
        expected_json = process_body_data(
            test_suite["expected_json"],
            parent_response
        )

    test_passed = True
    if host and path and expected_json:
        start_time = time.time()
        if not aux or verbose:
            print("Running %s... " % (name), end="")
        elif aux in ["setup", "teardown"]:
            print("Running auxillary %s request... " % (aux), end="")
        req = urllib.request.Request(
            host + path + "?" + urllib.parse.urlencode(
                get_body
            )
        )

        if post_body:
            req.add_header("Content-Type", "application/json")
            post_body = to_json(post_body).encode()
        response = urllib.request.urlopen(req, post_body)

        actual_json = from_json(response.read().decode())
        if "parent_response" not in test_suite:
            test_suite["parent_response"] = {}
        test_suite["parent_response"][identifier] = actual_json

        assert_error = is_expected_data(actual_json, expected_json, critical)
        elapse_time = time.time() - start_time
        if assert_error:
            if not aux or aux in ["setup", "teardown"] or verbose:
                print("failed (%.2fs)" % (elapse_time))
                if result_file:
                    result_file.write("%s|%s|%.2f|fail\n" % (
                        namespace, name, elapse_time
                    ))
            print(assert_error)
            if FLAGS["verbose"] or verbose:
                print(("=" * 10) + " FAILED " + ("=" * 10))
                print(represent_data(actual_json))
                print("-" * 28)
            if critical:
                test_passed = False
        else:
            if not aux or aux in ["setup", "teardown"] or verbose:
                print("passed (%.2fs)" % (elapse_time))
                if result_file:
                    result_file.write("%s|%s|%.2f|pass\n" % (
                        namespace, name, elapse_time
                    ))
            if FLAGS["verbose"] or verbose:
                print(("=" * 10) + " PASS " + ("=" * 10))
                print(represent_data(actual_json))
                print("-" * 26)

    if test_passed:
        if "tests" in test_suite:
            for test in test_suite["tests"]:
                run_test(
                    test,
                    namespace,
                    result_file,
                    critical,
                    test_suite,
                    (aux + "-sub") if aux else aux
                )
    if "teardown" in test_suite:
        run_test(
            test_suite["teardown"],
            namespace,
            result_file,
            False,
            test_suite,
            "teardown"
        )
    return test_passed


def run(args):
    if "--help" in args:
        print("Usages: %s [test file] [input file] [options]..." % (args[0]))
        print("Options:")
        print(
            "--help         : " +
            "show this message"
        )
        print(
            "--input <file> : " +
            "specified the input map file"
        )
        print(
            "--json         : " +
            "represent all object as in a JSON format"
        )
        print(
            "--no-result    : " +
            "do not generate testing result files (override config)"
        )
        print(
            "--result       : " +
            "generate testing result files (override config)"
        )
        print(
            "--verbose      : " +
            "print all the request and response body"
        )
        print(
            "--yaml         : " +
            "represent all object as in a YAML format"
        )
        return

    global INPUT_MAP, FLAGS
    input_file_name = None
    generate_result = None
    test_files = []

    if "--verbose" in args:
        FLAGS["verbose"] = True
        args.remove("--verbose")
    if "--json" in args:
        FLAGS["yaml"] = False
        args.remove("--json")
    if "--yaml" in args:
        FLAGS["yaml"] = True
        args.remove("--yaml")
    if "--result" in args:
        generate_result = True
        args.remove("--result")
    if "--no-result" in args:
        generate_result = False
        args.remove("--no-result")
    if "--input" in args:
        index = args.index("--input") + 1
        if index < len(args):
            input_file_name = args[index]
            args.remove(input_file_name)
        args.remove("--input")

    if len(args) < 2:
        if not os.path.exists(TEST_SUITE_FILE_NAME):
            print("No test suite found")
            exit(1)
        test_suite_file = open(TEST_SUITE_FILE_NAME, "r", encoding="utf-8")
        test_suite = load_data(test_suite_file.read())
        test_suite_file.close()
        if "run_test" in test_suite and not test_suite["run_test"]:
            print("Skip testing")
            exit(0)
        if "input" in test_suite:
            input_file_name = input_file_name or test_suite["input"]
        if generate_result is None and "generate_result" in test_suite:
            generate_result = test_suite["generate_result"]
        if "tests" in test_suite:
            test_files = test_suite["tests"]
        print(":: Test suite loaded [%s tests] ::" % (len(test_files)))
    else:
        test_files.append(args[1])
        if len(args) > 2:
            input_file_name = input_file_name or args[2]
            args.remove(input_file_name)

    generate_result = generate_result or False

    if input_file_name and os.path.exists(input_file_name):
        input_file = open(input_file_name, "r", encoding="utf-8")
        INPUT_MAP = load_data(input_file.read())
        input_file.close()
        print(":: Input loaded: %s ::" % (input_file_name))

    test_passed = True
    result_file = None
    if generate_result:
        result_file = open(
            TEST_RESULT_FILE_NAME,
            "w",
            encoding="utf-8"
        )
    for test_file_name in test_files:
        if not os.path.exists(test_file_name):
            print(":: Test is not found: %s ::" % (test_file_name))
            continue
        test_file = open(test_file_name, "r", encoding="utf-8")
        test = load_data(test_file.read())
        test_file.close()
        print(":: Test loaded: %s ::" % (test_file_name))

        file_name = os.path.splitext(os.path.basename(test_file_name))[0]
        if not run_test(process_macro(test), file_name, result_file):
            test_passed = False
    if generate_result:
        result_file.close()
    exit(0 if test_passed else 1)

if __name__ == "__main__":
    run(sys.argv)
