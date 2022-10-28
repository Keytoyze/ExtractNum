import argparse
import csv
import json
import re
import sys

import matplotlib.pyplot as plt
import numpy as np

verbose = False


def on_error(text):
    print(text, file=sys.stderr)
    exit(-1)


def debug(text):
    global verbose
    if verbose:
        print('[D]', text)


def parse_plain_pattern(pattern, placehold_pattern):
    escape_pattern = re.escape(pattern)
    regex_pattern = escape_pattern.replace("\\{", "(?P<").replace("\\}",
                                                                  ">" + placehold_pattern + ")")
    debug(f"Compile pattern: '{pattern}' -> '{regex_pattern}'.")
    return re.compile(regex_pattern)


def to_rows(label_to_array, labels):
    rows = []
    nan = float("nan")
    i = 0
    while True:
        end = True
        row = []
        for label in labels:
            if len(label_to_array[label]) <= i:
                row.append(nan)
            else:
                end = False
                row.append(label_to_array[label][i])
        if end:
            break
        i += 1
        rows.append(row)
    return rows


def smooth(scalars, weight):
    last = scalars[0]
    smoothed = list()
    for point in scalars:
        smoothed_val = last * weight + (1 - weight) * point
        smoothed.append(smoothed_val)
        last = smoothed_val

    return smoothed


def plot(label_to_array, args):
    if args.x == "":
        x = None
    else:
        if args.x not in label_to_array:
            on_error(f"Cannot find the label {args.x}. "
                     f"Please check if one of the patterns contains {args.x}.")
        x = list(label_to_array[args.x])
        del label_to_array[args.x]
    for label, array in label_to_array.items():
        if x is None:
            x = np.arange(len(array))
        else:
            if len(x) > len(array):
                x = x[:len(array)]
            elif len(x) < len(array):
                on_error(f"X array length ({len(x)}) < the array {label} length ({len(array)}!")
        plt.plot(x, smooth(array, args.smooth), label=label)
    plt.legend()
    plt.tight_layout()


def write_text(args, extension, text):
    if extension == 'txt':
        with open(args.output, "w") as f:
            f.write(text)
    else:
        print(text)


def to_number_if_possible(x):
    try:
        return float(x)
    except:
        return x


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=argparse.FileType(mode='r'), help="Text file path to parse")
    parser.add_argument("--pattern", "-p", type=str, nargs='+', default=[],
                        metavar="<number pattern>",
                        help='Pattern for extracting real numbers from log. '
                             "For example, for a log line 'training acc: 3.14%%', a pattern "
                             "'acc: {accuracy}' will extract 3.14, and plot it with a label "
                             "'accuracy'. Note that this pattern could only handle simple case. "
                             "For a more complicated case, please turn on --regex mode.")
    parser.add_argument("--x", type=str, default="", metavar="<label>",
                        help='Specify a label as the X array for plotting. For example, if there '
                             'exists an array with a label "iteration", you can use "--x iteration" '
                             'to make this array as the plotting X array. Not that the label should '
                             'be in one of the patterns. By default, a sequence of natural numbers '
                             'will be used.')
    parser.add_argument("--regex", action='store_true',
                        help='Regex mode. If enable, patterns will be interpreted as regex patterns. '
                             "For example, for a log line 'training acc: 3.14%%', a pattern "
                             "'acc:\s(?P<accuracy>[+|-]?\d*(\.\d*)?)' will extract 3.14, and plot "
                             "it with a label 'accuracy'.")
    parser.add_argument("--placehold_pattern", type=str, default="[+|-]?\d*(\.\d*)?",
                        metavar="<regex>",
                        help='The regex to replace the placeholder label. By default, a real '
                             'number regex is used: "[+|-]?\d*(\.\d*)?".')
    parser.add_argument("--output", "-o", type=str, metavar="<path>", default=None,
                        help='Output path. It supports the following types: '
                             '(1) Any image format that matplotlib supports: save as an image file. '
                             '(2) *.csv: save as a csv table format. '
                             '(3) *.json: save as a json format. '
                             '(4) *.txt / stdout: print a table to a text file or the standard output. '
                             '(5) otherwise, show a matplotlib image window. ')
    parser.add_argument("--smooth", type=float, default=0.0, metavar="<weight>",
                        help='Perform exponential moving average to smooth values when plotting. '
                             'Default: 0')
    parser.add_argument("--offset", type=int, default=0, metavar="<offset>",
                        help='The number of skipping lines before parsing. Default: 0')
    parser.add_argument("--limit", type=int, default=0, metavar="<limit>",
                        help='Max numbers for each label in parsing. 0 indicates no limits. Default: 0')
    parser.add_argument("--verbose", '-v', action='store_true',
                        help='Verbose mode.')

    args = parser.parse_args()

    global verbose
    verbose = args.verbose

    if len(args.pattern) == 0:
        on_error("You should specify at lease a pattern.")
    patterns = []
    if args.regex:
        for p in args.pattern:
            try:
                patterns.append(re.compile(p))
            except re.error as e:
                on_error(f"Cannot parse the regex pattern: '{p}'. Error: {str(e)}")
    else:
        for p in args.pattern:
            try:
                patterns.append(parse_plain_pattern(p, args.placehold_pattern))
            except re.error as e:
                on_error(f"Cannot parse the plain pattern: '{p}'. Error: {str(e)}")

    # parse
    label_to_array = {}
    current_line = -1
    for line in args.file:
        current_line += 1
        if current_line < args.offset:
            continue
        # Substitute multiple whitespace with single whitespace
        _RE_COMBINE_WHITESPACE = re.compile(r"\s+")
        line = _RE_COMBINE_WHITESPACE.sub(" ", line).strip()
        for p in patterns:
            result = p.search(line)
            if result is not None:
                for label, value in result.groupdict().items():
                    if label not in label_to_array:
                        label_to_array[label] = []
                    if args.limit == 0 or len(label_to_array[label]) < args.limit:
                        label_to_array[label].append(to_number_if_possible(value))
    if len(label_to_array) == 0:
        on_error("No any number found. Please check it.")

    # output
    extension = args.output.split(".")[-1] if "." in args.output else args.output
    if extension in plt.gcf().canvas.get_supported_filetypes():
        plot(label_to_array, args)
        plt.savefig(args.output)
    elif extension == 'csv':
        labels = list(label_to_array.keys())
        rows = to_rows(label_to_array, labels)
        with open(args.output, "w", newline="") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(labels)
            csv_writer.writerows(rows)
    elif extension == 'json':
        with open(args.output, "w") as f:
            json.dump(label_to_array, f)
    elif extension == 'txt' or extension == 'stdout':
        labels = list(label_to_array.keys())
        rows = to_rows(label_to_array, labels)
        try:
            debug("Try to use pandas...")
            import pandas as pd
            df = pd.DataFrame(rows, columns=labels)
            write_text(args, extension, df.to_string())
        except ImportError:
            debug("pandas not found. Use a horizontal tab character to split columns.")
            lines = ["\t".join(labels)]
            lines.extend(["\t".join(map(str, x)) for x in rows])
            write_text(args, extension, "\n".join(lines))
    else:
        plot(label_to_array, args)
        plt.show()


if __name__ == "__main__":
    main()
