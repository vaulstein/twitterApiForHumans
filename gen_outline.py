#!/usr/bin/env python

import json
import os, os.path


def key_paths(d):
    def helper(path, x):
        if isinstance(x, dict):
            for k, v in x.iteritems():
                for ret in helper(path + [k], v):
                    yield ret
        elif isinstance(x, list):
            for i, item in enumerate(x):
                for ret in helper(path + [i], item):
                    yield ret
        else:
            yield path
    return helper([], d)


def line_iter(f):
    for line in f:
        yield json.loads(line)


def coll_iter(f, coll_key):
    data = json.load(f)
    for obj in data[coll_key]:
        yield obj


def gather_key_map(iterator):
    key_map = {}
    for d in iterator:
        for path in key_paths(d):
            key_map[tuple(path)] = True
    return key_map


def path_join(path, sep='.'):
    return sep.join(str(k) for k in path)


def key_map_to_list(key_map):
    # We convert to strings *after* sorting so that array indices come out
    # in the correct order.
    return [(path_join(k, '_'), path_join(k)) for k in sorted(key_map.keys())]


def make_outline(json_file, each_line, collection_key):
    if each_line:
        iterator = line_iter(json_file)
    else:
        iterator = coll_iter(json_file, collection_key)

    key_map = gather_key_map(iterator)
    outline = {'map': key_map_to_list(key_map)}
    if collection_key:
        outline['collection'] = collection_key

    return outline