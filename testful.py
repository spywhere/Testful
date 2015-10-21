#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: spywhere
# @Date:   2015-10-02 09:54:10
# @Last Modified by:   Sirisak Lueangsaksri
# @Last Modified time: 2015-10-21 17:05:03

import base64
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
MACRO_PATTERN = re.compile("<%(\\w+)(:(((%[^>])|[^%>])*))?%>")
DATA_PATTERN = re.compile("<<([\\w-]+(\\.[\\w-]+)*)>>")
TEST_SUITE_FILE_NAME = "test_config.yaml"
TEST_RESULT_FILE_NAME = "results.testful"
DEFAULT_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def load_data(raw_data):
    return yaml.load(raw_data)


def represent_data(data):
    if FLAGS["yaml"]:
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
    else:
        return json.dumps(data, indent="  ", ensure_ascii=False)


def save_data(data, out_file=None):
    if out_file:
        return yaml.dump(data, out_file, allow_unicode=True, default_flow_style=False, canonical=True)
    else:
        return yaml.dump(data, allow_unicode=True, canonical=True)


def from_json(raw_data):
    return json.loads(raw_data)


def to_json(data):
    return json.dumps(data)


def time_from_string(time_str):
    match = re.match(
        (
            "((?P<day>-?\\d+)d)?((?P<hour>-?\\d+)h)?" +
            "((?P<min>-?\\d+)m)?((?P<sec>-?\\d+)s)?" +
            "((?P<ms>-?\\d+)ms)?"
        ), time_str
    )
    success = False
    duration = 0
    if match:
        if match.group("day"):
            success = True
            duration += int(match.group("day")) * 86400
        if match.group("hour"):
            success = True
            duration += int(match.group("hour")) * 3600
        if match.group("min"):
            success = True
            duration += int(match.group("min")) * 60
        if match.group("sec"):
            success = True
            duration += int(match.group("sec"))
        if match.group("ms"):
            success = True
            duration += float(match.group("ms") / 1000)
    if success:
        return duration
    else:
        return None


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


def gather_special_macro(name, dtformat):
    if name == "datetime":
        current_time = time.time()
        if not dtformat:
            dtformat = time.strftime(DEFAULT_DATE_TIME_FORMAT)
        formats = dtformat.split(":")
        diff = time_from_string(formats[-1])
        if len(formats) > 1 and diff is not None:
            dtformat = ":".join(formats[:-1])
        else:
            diff = 0
            dtformat = ":".join(formats)
        return time.strftime(
            dtformat,
            time.localtime(current_time + diff)
        )
    return ""


def gather_macro(key, modifier=None):
    global INPUT_LINES, MACROS
    if key in MACROS:
        return MACROS[key]
    if key in SPECIAL_MACROS:
        return gather_special_macro(key, modifier)
    if key in INPUT_MAP:
        value = str(INPUT_MAP[key])
        print("%s: %s" % (key, value))
    else:
        value = input(key + ": ")
    if modifier and modifier == "base64":
        value = base64.encodestring(value.encode()).decode().strip()
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


def process_post_body(body):
    processed_body = {}
    for key, value in body.items():
        if isinstance(value, dict):
            value = process_post_body(value)
        if key.endswith("_raw"):
            key = key[:-4]
        elif key.endswith("_escaped") and isinstance(value, dict):
            key = key[:-8]
            value = to_json(value)
        processed_body[key] = value
    return processed_body


def run_test(test_suite, namespace, result_file=None, results=None,
             critical=True, parent=None, aux=None):
    parent = parent or {}
    parent_response = {}
    if "parent_response" in parent:
        parent_response = parent["parent_response"]
    host = ""
    verbose_on_failed = (
        "verbose_on_failed" in parent and parent["verbose_on_failed"]
    )
    if "verbose_on_failed" in test_suite:
        verbose_on_failed = test_suite["verbose_on_failed"]
    test_suite["verbose_on_failed"] = verbose_on_failed
    verbose = "verbose" in parent and parent["verbose"]
    if ("allow_verbose_override" not in parent or
            not parent["allow_verbose_override"]) and "verbose" in test_suite:
        verbose = test_suite["verbose"]
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
    skipped = "skip" in test_suite and test_suite["skip"]
    timeout = None
    if "timeout" in parent:
        timeout = parent["timeout"]
    if "timeout" in test_suite:
        timeout = test_suite["timeout"]
    test_suite["timeout"] = timeout
    headers = {}
    get_body = {}
    post_body = None
    json_body = None
    expected_json = {}
    if not skipped and "setup" in test_suite:
        setup_status = run_test(
            test_suite["setup"],
            namespace,
            result_file,
            results,
            False,
            parent,
            "setup"
        )
        if not setup_status:
            return False
    if not skipped and "get" in test_suite:
        get_body = process_body_data(
            test_suite["get"],
            parent_response
        )
        if FLAGS["verbose"] or verbose:
            print(("=" * 10) + " GET " + ("=" * 10))
            print(represent_data(get_body))
            print("-" * 25)
    if not skipped and "json_post" in test_suite:
        json_body = process_body_data(
            test_suite["json_post"],
            parent_response
        )
        if FLAGS["verbose"] or verbose:
            print(("=" * 10) + " JSON POST " + ("=" * 10))
            print(represent_data(json_body))
            print("-" * 26)
    if not skipped and "post" in test_suite:
        post_body = process_post_body(process_body_data(
            test_suite["post"],
            parent_response
        ))
        if FLAGS["verbose"] or verbose:
            print(("=" * 10) + " POST " + ("=" * 10))
            print(represent_data(post_body))
            print("-" * 26)
    if "headers" in parent:
        headers.update(process_body_data(
            parent["headers"],
            parent_response
        ))
    if "headers" in test_suite:
        headers.update(process_body_data(
            test_suite["headers"],
            parent_response
        ))
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
        if skipped:
            print("skipped")
            if results:
                results["skip"] += 1
            if result_file:
                result_file.write("%s|%s|%.2f|skip\n" % (
                    namespace, name, 0
                ))
            return True
        req = urllib.request.Request(
            host + path + "?" + urllib.parse.urlencode(
                get_body, True
            )
        )

        for key, value in headers.items():
            req.add_header(key, value)

        if post_body:
            post_body = urllib.parse.urlencode(post_body, True).encode()
        elif json_body:
            req.add_header("Content-Type", "application/json")
            post_body = to_json(json_body).encode()
        try:
            response = urllib.request.urlopen(req, post_body, timeout)
            actual_json = from_json(response.read().decode())
            if "parent_response" not in test_suite:
                test_suite["parent_response"] = {}
            test_suite["parent_response"][identifier] = actual_json

            assert_error = is_expected_data(actual_json, expected_json, critical)
        except Exception as e:
            assert_error = str(e)
            actual_json = None

        elapse_time = time.time() - start_time
        if assert_error:
            if not aux or aux in ["setup", "teardown"] or verbose:
                print("failed (%.2fs)" % (elapse_time))
                if results:
                    results["fail"] += 1
                if result_file:
                    result_file.write("%s|%s|%.2f|fail\n" % (
                        namespace, name, elapse_time
                    ))
            print(assert_error)
            if FLAGS["verbose"] or verbose or verbose_on_failed:
                print(("=" * 10) + " FAILED " + ("=" * 10))
                if actual_json is not None:
                    print(represent_data(actual_json))
                    print("-" * 28)
            if critical:
                test_passed = False
        else:
            if not aux or aux in ["setup", "teardown"] or verbose:
                print("passed (%.2fs)" % (elapse_time))
                if results:
                    results["pass"] += 1
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
                    results,
                    critical,
                    test_suite,
                    (aux + "-sub") if aux else aux
                )
    if "teardown" in test_suite:
        run_test(
            test_suite["teardown"],
            namespace,
            result_file,
            results,
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
            "--config <file> : " +
            "specified the test configuration file"
        )
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
    test_suite_file_name = TEST_SUITE_FILE_NAME
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
    if "--config" in args:
        index = args.index("--config") + 1
        if index < len(args):
            test_suite_file_name = args[index]
            args.remove(test_suite_file_name)
        args.remove("--config")
    if "--input" in args:
        index = args.index("--input") + 1
        if index < len(args):
            input_file_name = args[index]
            args.remove(input_file_name)
        args.remove("--input")

    if len(args) < 2:
        if not os.path.exists(test_suite_file_name):
            print("No test suite found")
            exit(1)
        test_suite_file = open(test_suite_file_name, "r", encoding="utf-8")
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
    results = {
        "pass": 0,
        "skip": 0,
        "fail": 0
    }
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
        if not run_test(process_macro(test), file_name, result_file, results):
            test_passed = False
    if generate_result:
        result_file.close()
    print("=" * 40)
    print("Total tests run: %s, Failures: %s, Skips: %s" % (
        sum([results[k] for k in results]), results["fail"], results["skip"]
    ))
    print("=" * 40)
    exit(0 if test_passed else 1)

if __name__ == "__main__":
    run(sys.argv)
