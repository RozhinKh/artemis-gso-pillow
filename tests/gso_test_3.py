import timeit
import json
import os
import hashlib
import numpy as np
from PIL import Image

def setup():
    """
    Generate a collection of random images with different modes and odd/even sizes,
    to trigger various code paths (corners, Nx1, 1xN, NxN, etc.) in Image.reduce.
    Returns a dict of PIL Images keyed by descriptive names.
    """
    np.random.seed(12345)
    images = {}
    # 1) Grayscale, odd dimensions to test corner pixels
    w1, h1 = 1023, 769
    arr1 = np.random.randint(0, 256, (h1, w1), dtype=np.uint8)
    images[f"L_{w1}x{h1}"] = Image.fromarray(arr1, mode="L")
    # 2) RGB, mixed divisibility
    w2, h2 = 2048, 1536
    arr2 = np.random.randint(0, 256, (h2, w2, 3), dtype=np.uint8)
    images[f"RGB_{w2}x{h2}"] = Image.fromarray(arr2, mode="RGB")
    # 3) RGBA, one dimension not divisible by common factors
    w3, h3 = 1001, 1000
    arr3 = np.random.randint(0, 256, (h3, w3, 4), dtype=np.uint8)
    images[f"RGBA_{w3}x{h3}"] = Image.fromarray(arr3, mode="RGBA")
    return images

def experiment(images):
    """
    For each input image and a variety of reduction factors, call Image.reduce()
    and record essential properties for equivalence checking.
    """
    results = {}
    factors = [2, 3, 5, 7]
    for name, img in images.items():
        for factor in factors:
            # skip trivial cases where factor is larger than dimension
            if factor > img.width or factor > img.height:
                continue
            reduced = img.reduce(factor)
            key = f"{name}_f{factor}"
            # checksum of raw bytes to detect any pixel changes
            checksum = hashlib.md5(reduced.tobytes()).hexdigest()
            results[key] = {
                "mode": reduced.mode,
                "size": reduced.size,  # PIL gives a tuple
                "checksum": checksum
            }
    return results

def store_result(result, filename):
    """
    Store the experiment result dict into a JSON file.
    """
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

def load_result(filename):
    """
    Load the experiment result dict from a JSON file.
    """
    with open(filename, 'r') as f:
        return json.load(f)

def check_equivalence(ref_result, current_result):
    """
    Assert that the current_result matches the ref_result exactly in keys,
    image modes, sizes, and checksums.
    """
    assert set(ref_result.keys()) == set(current_result.keys()), \
        f"Keys differ. Ref: {sorted(ref_result.keys())}, Current: {sorted(current_result.keys())}"
    for key in ref_result:
        ref = ref_result[key]
        cur = current_result[key]
        # compare mode
        assert ref["mode"] == cur["mode"], \
            f"Mode mismatch for {key}: {ref['mode']} vs {cur['mode']}"
        # compare size (tuple vs list)
        ref_size = tuple(ref["size"]) if isinstance(ref["size"], list) else ref["size"]
        cur_size = tuple(cur["size"]) if isinstance(cur["size"], list) else cur["size"]
        assert ref_size == cur_size, \
            f"Size mismatch for {key}: {ref_size} vs {cur_size}"
        # compare checksum
        assert ref["checksum"] == cur["checksum"], \
            f"Checksum mismatch for {key}: {ref['checksum']} vs {cur['checksum']}"

def run_test(eqcheck: bool = False, reference: bool = False, prefix: str = '') -> float:
    """
    Orchestrate setup, timing of the experiment, and optional storing or
    equivalence checking against a reference result.
    """
    images = setup()  # not timed

    # time the experiment; number=1 is sufficient given large images
    execution_time, result = timeit.timeit(lambda: experiment(images), number=1)

    # determine reference filename
    ref_file = f"{prefix}_result.json" if prefix else "reference_result.json"
    if reference:
        store_result(result, ref_file)
    if eqcheck:
        ref = load_result(ref_file)
        check_equivalence(ref, result)

    return execution_time

timeit.template = """
def inner(_it, _timer{init}):
    {setup}
    _t0 = _timer()
    for _i in _it:
        retval = {stmt}
    _t1 = _timer()
    return _t1 - _t0, retval
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Measure performance of API.')
    parser.add_argument('output_file', type=str, help='File to append timing results to.')
    parser.add_argument('--eqcheck', action='store_true', help='Enable equivalence checking')
    parser.add_argument('--reference', action='store_true', help='Store result as reference instead of comparing')
    parser.add_argument('--file_prefix', type=str, help='Prefix for any file where reference results are stored')
    args = parser.parse_args()

    # Measure the execution time
    execution_time = run_test(args.eqcheck, args.reference, args.file_prefix)

    # Append the results to the specified output file
    with open(args.output_file, 'a') as f:
        f.write(f'Execution time: {execution_time:.6f}s\n')

if __name__ == '__main__':
    main()


timeit.template = """
def inner(_it, _timer{init}):
    {setup}
    _t0 = _timer()
    for _i in _it:
        retval = {stmt}
    _t1 = _timer()
    return _t1 - _t0, retval
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Measure performance of API.')
    parser.add_argument('output_file', type=str, help='File to append timing results to.')
    parser.add_argument('--eqcheck', action='store_true', help='Enable equivalence checking')
    parser.add_argument('--reference', action='store_true', help='Store result as reference instead of comparing')
    parser.add_argument('--file_prefix', type=str, help='Prefix for any file where reference results are stored')
    args = parser.parse_args()

    # Measure the execution time
    execution_time = run_test(args.eqcheck, args.reference, args.file_prefix)

    # Append the results to the specified output file
    with open(args.output_file, 'a') as f:
        f.write(f'Execution time: {execution_time:.6f}s\n')

if __name__ == '__main__':
    main()
