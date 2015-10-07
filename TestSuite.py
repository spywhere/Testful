#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: spywhere
# @Date:   2015-10-02 09:54:10
# @Last Modified by:   Sirisak Lueangsaksri
# @Last Modified time: 2015-10-06 18:10:31

import json
import re
import sys
import time
import urllib.request

FLAGS = {
    "verbose": False
}
SPECIAL_MACROS = ["datetime"]
MACROS = {}
MACRO_PATTERN = re.compile("<%(\\w+)(:(.*[^%>]))?%>")
DATA_PATTERN = re.compile("<<([\\w-]+(\\.[\\w-]+)*)>>")


def is_expected_json(actual, expect, critical=True, last_key=None):
    last_key = last_key or []
    if type(actual) != type(expect):
        return "Expected \"%s\" but got \"%s\" instead" % (expect, actual)

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
                        "actual dict"
                        if not last_key
                        else ("\"%s\" key" % (".".join(last_key)))
                    )
            else:
                return is_expected_json(
                    actual[ex_key],
                    ex_val,
                    critical,
                    last_key + [str(ex_key)]
                )
            if (isinstance(ex_val, dict) or isinstance(ex_val, list) or
                    isinstance(ex_val, tuple)):
                return is_expected_json(
                    actual[ex_key],
                    expect[ex_key],
                    critical,
                    last_key + [str(ex_key)]
                )
            assert_error = is_expected_json(
                actual[ex_key],
                ex_val,
                critical,
                last_key + [str(ex_key)]
            )
            if assert_error:
                return assert_error
        return None
    else:
        if actual == expect:
            return None
        else:
            return "Expected \"%s\"%s but got \"%s\" instead" % (
                expect, ""
                if not last_key
                else (" in the \"%s\"" % (".".join(last_key))), actual
            )


def gather_special_macro(name, format):
    if name == "datetime":
        if format:
            return time.strftime(format)
        else:
            return str(int(time.time()))
    return ""


def gather_macro(key, type=None):
    if key in SPECIAL_MACROS:
        return gather_special_macro(key, type)
    global MACROS
    if key in MACROS:
        return MACROS[key]
    value = input(key + ": ")
    MACROS[key] = value
    return value


def process_macro(body):
    json_data = json.dumps(body)
    json_data = MACRO_PATTERN.sub(
        lambda m: gather_macro(m.group(1), m.group(3)),
        json_data
    )
    return json.loads(json_data)


def gather_data(data, key, root=True):
    keys = key.split(".")
    if not keys:
        return data
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
        return data


def process_raw_data(body, data):
    return DATA_PATTERN.sub(
        lambda m: gather_data(data, m.group(1)),
        body
    )


def process_body_data(body, data):
    json_data = json.dumps(body)
    return json.loads(process_raw_data(json_data, data))


def run_test(test_suite, critical=True, parent=None, aux=None):
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
        setup_error = run_test(
            test_suite["setup"],
            False,
            parent,
            "setup"
        )
        if setup_error:
            return False
    if "get" in test_suite:
        get_body = process_body_data(
            test_suite["get"],
            parent_response
        )
        if FLAGS["verbose"] or verbose:
            print(("=" * 10) + " GET " + ("=" * 10))
            print(json.dumps(get_body, indent="  ", ensure_ascii=False))
            print("-" * 25)
    if "post" in test_suite:
        post_body = process_body_data(
            test_suite["post"],
            parent_response
        )
        if FLAGS["verbose"] or verbose:
            print(("=" * 10) + " POST " + ("=" * 10))
            print(json.dumps(post_body, indent="  ", ensure_ascii=False))
            print("-" * 26)

    if "expected_json" in test_suite:
        expected_json = process_body_data(
            test_suite["expected_json"],
            parent_response
        )

    if host and path and expected_json:
        if not aux:
            print("Running %s... " % (name), end="")
        else:
            print("Running auxillary %s request... " % (aux), end="")
        req = urllib.request.Request(
            host + path + "?" + urllib.parse.urlencode(
                get_body
            )
        )

        if post_body:
            req.add_header("Content-Type", "application/json")
            post_body = json.dumps(post_body).encode()
        response = urllib.request.urlopen(req, post_body)

        actual_json = json.loads(response.read().decode())
        if "parent_response" not in test_suite:
            test_suite["parent_response"] = {}
        test_suite["parent_response"][identifier] = actual_json

        assert_error = is_expected_json(actual_json, expected_json, critical)
        if "teardown" in test_suite:
            run_test(
                test_suite["teardown"],
                False,
                test_suite,
                "teardown"
            )
        if assert_error:
            print("failed")
            print(assert_error)
            if FLAGS["verbose"] or verbose:
                print(("=" * 10) + " FAILED " + ("=" * 10))
                print(json.dumps(actual_json, indent="  ", ensure_ascii=False))
                print("-" * 28)
            if critical:
                return False
        else:
            print("pass")
            if FLAGS["verbose"] or verbose:
                print(("=" * 10) + " PASS " + ("=" * 10))
                print(json.dumps(actual_json, indent="  ", ensure_ascii=False))
                print("-" * 26)

    if "tests" in test_suite:
        for test in test_suite["tests"]:
            if not run_test(test, critical, test_suite):
                return False
    return True


def run(args):
    if "--verbose" in args:
        global FLAGS
        FLAGS["verbose"] = True
        args.remove("--verbose")
    if len(args) < 2:
        print("Usages: %s <test suite file>" % (args[0]))
        return
    test_suite_file = open(args[1], "r")
    test_suite = json.load(test_suite_file)
    test_suite_file.close()

    print("Test suite loaded: " + args[1])

    if not run_test(process_macro(test_suite)):
        exit(1)

if __name__ == "__main__":
    run(sys.argv)
