"""Impact Pack compatible wildcard expansion.

The expansion functions below are adapted from ComfyUI-Impact-Pack's
modules/impact/wildcards.py at commit 429d0159ad429e64d2b3916e6e7be9c22d025c3c.
Original project: https://github.com/ltdrdata/ComfyUI-Impact-Pack
Original license: GPL-3.0. This file is also GPL-3.0.

Changes: load wildcard files without importing Impact Pack, reload edited files,
and avoid changing Python's process-wide random state.
"""

import configparser
import logging
import re
import threading
from pathlib import Path

import numpy as np
import yaml


RE_WildCardQuantifier = re.compile(r"(?P<quantifier>\d+)#__(?P<keyword>[\w.\-+/*\\]+?)__", re.IGNORECASE)
_lock = threading.RLock()
_signature = None
wildcard_dict = {}
available_wildcards = {}
_on_demand_mode = False


def wildcard_normalize(value):
    return value.replace("\\", "/").replace(" ", "-").lower()


def _wildcard_roots():
    here = Path(__file__).resolve().parent
    impact = here.parent / "ComfyUI-Impact-Pack"
    roots = [impact / "wildcards"]

    config = configparser.ConfigParser()
    config.read(impact / "impact-pack.ini", encoding="utf-8")
    custom = config.get("default", "custom_wildcards", fallback="").strip("\"'")
    custom_path = Path(custom) if custom else impact / "custom_wildcards"
    if not custom_path.is_dir():
        custom_path = impact / "custom_wildcards"
    roots.append(custom_path)
    roots.extend((here / "wildcards", here / "custom_wildcards"))
    return roots


def _read_text(path):
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="iso-8859-1")


def _read_yaml_values(result, prefix, value):
    if isinstance(value, dict):
        for name, child in value.items():
            key = f"{prefix}/{name}" if prefix else str(name)
            _read_yaml_values(result, key, child)
    elif isinstance(value, list):
        result[wildcard_normalize(prefix)] = [str(item) for item in value]
    elif isinstance(value, (str, int, float)):
        result[wildcard_normalize(prefix)] = [str(value)]


def refresh_wildcards():
    global _signature, wildcard_dict, available_wildcards

    files = []
    for root in _wildcard_roots():
        if root.is_dir():
            files.extend(sorted(path for path in root.rglob("*") if path.suffix.lower() in (".txt", ".yaml", ".yml") and path.is_file()))
    signature = tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in files)

    with _lock:
        if signature == _signature:
            return _signature
        values = {}
        for path in files:
            try:
                if path.suffix.lower() == ".txt":
                    root = next(root for root in _wildcard_roots() if path.is_relative_to(root))
                    key = wildcard_normalize(str(path.relative_to(root).with_suffix("")))
                    values[key] = [line for line in _read_text(path).splitlines() if line.strip() and not line.lstrip().startswith("#")]
                else:
                    _read_yaml_values(values, "", yaml.load(_read_text(path), Loader=yaml.FullLoader) or {})
            except (OSError, yaml.YAMLError, ValueError) as exc:
                logging.warning("[wild-card] Cannot load %s: %s", path, exc)
        wildcard_dict = values
        available_wildcards = values
        _signature = signature
        return _signature


def get_wildcard_dict():
    return wildcard_dict


def get_wildcard_value(key):
    return wildcard_dict.get(key)


def process_comment_out(text):
    lines = text.split('\n')

    lines0 = []
    flag = False
    for line in lines:
        if line.lstrip().startswith('#'):
            flag = True
            continue

        if len(lines0) == 0:
            lines0.append(line)
        elif flag:
            lines0[-1] += ' ' + line
            flag = False
        else:
            lines0.append(line)

    return '\n'.join(lines0)


def process(text, seed=None):
    text = process_comment_out(text)

    random_gen = np.random.default_rng(seed)

    local_wildcard_dict = get_wildcard_dict()

    def replace_options(string):
        replacements_found = False

        def replace_option(match):
            nonlocal replacements_found
            options = match.group(1).split('|')

            multi_select_pattern = options[0].split('$$')
            select_range = None
            select_sep = ' '
            range_pattern = r'(\d+)(-(\d+))?'
            range_pattern2 = r'-(\d+)'
            wildcard_pattern = r"__([\w.\-+/*\\]+?)__"

            if len(multi_select_pattern) > 1:
                r = re.match(range_pattern, options[0])

                if r is None:
                    r = re.match(range_pattern2, options[0])
                    a = '1'
                    b = r.group(1).strip()
                else:
                    a = r.group(1).strip()
                    b = r.group(3)
                    if b is not None:
                        b = b.strip()
                    else:
                        b = a

                if r is not None:
                    if b is not None and is_numeric_string(a) and is_numeric_string(b):
                        # PATTERN: num1-num2
                        select_range = int(a), int(b)
                    elif is_numeric_string(a):
                        # PATTERN: num
                        x = int(a)
                        select_range = (x, x)

                    # Expand wildcard path or return the string after $$
                    def expand_wildcard_or_return_string(options, pattern, wildcard_pattern):
                        matches = re.findall(wildcard_pattern, pattern)
                        if len(options) == 1 and matches:
                            # $$<single wildcard>
                            return get_wildcard_options(pattern)
                        else:
                            # $$opt1|opt2|...
                            options[0] = pattern
                            return options

                    if select_range is not None and len(multi_select_pattern) == 2:
                        # PATTERN: count$$
                        options = expand_wildcard_or_return_string(options, multi_select_pattern[1], wildcard_pattern )
                    elif select_range is not None and len(multi_select_pattern) == 3:
                        # PATTERN: count$$ sep $$
                        select_sep = multi_select_pattern[1]
                        options = expand_wildcard_or_return_string(options, multi_select_pattern[2], wildcard_pattern )

            adjusted_probabilities = []

            total_prob = 0

            for option in options:
                parts = option.split('::', 1) if isinstance(option, str) else f"{option}".split('::', 1)

                if len(parts) == 2 and is_numeric_string(parts[0].strip()):
                    config_value = float(parts[0].strip())
                else:
                    config_value = 1  # Default value if no configuration is provided

                adjusted_probabilities.append(config_value)
                total_prob += config_value

            normalized_probabilities = [prob / total_prob for prob in adjusted_probabilities]

            if select_range is None:
                select_count = 1
            else:
                def calculate_max(_options_length, _max_select_range):
                    return min(_max_select_range + 1, _options_length + 1) if _max_select_range > 0 else _options_length + 1

                def calculate_select_count(_max_value, _min_select_range, random_gen):
                    if max(_max_value, _min_select_range) <= 0:
                        return 0
                    # fix: low >= high
                    elif _max_value == _min_select_range:
                        return _max_value
                    else:
                        # fix: low >= high
                        _low_value = min(_min_select_range, _max_value)
                        _high_value = max(_min_select_range, _max_value)
                        return random_gen.integers(low=_low_value, high=_high_value, size=1)
                select_count = calculate_select_count(calculate_max(len(options), select_range[1]), select_range[0], random_gen)

            if select_count > len(options) or total_prob <= 1:
                random_gen.shuffle(options)
                selected_items = options
            else:
                selected_items = random_gen.choice(options, p=normalized_probabilities, size=select_count, replace=False)

            # x may be numpy.int32, convert to string
            selected_items2 = [re.sub(r'^\s*[0-9.]+::', '', str(x), count=1) for x in selected_items]
            replacement = select_sep.join(selected_items2)
            if '::' in replacement:
                pass

            replacements_found = True
            return replacement

        pattern = r'(?<!\\)\{((?:[^{}]|(?<=\\)[{}])*?)(?<!\\)\}'
        replaced_string = re.sub(pattern, replace_option, string)

        return replaced_string, replacements_found

    def get_wildcard_options(string):
        pattern = r"__([\w.\-+/*\\]+?)__"
        matches = re.findall(pattern, string)

        options = []

        for match in matches:
            keyword = match.lower()
            keyword = wildcard_normalize(keyword)

            if '*' in keyword:
                logging.debug(f"[wild-card] [get_wildcard_options] Processing wildcard pattern: keyword={keyword}")

            # Use get_wildcard_value for on-demand loading support
            wildcard_value = get_wildcard_value(keyword)

            if wildcard_value is not None:
                options.extend(wildcard_value)
            elif '*' in keyword:
                total_patterns = []
                found = False

                # For wildcard patterns, search through available wildcards
                search_dict = available_wildcards if _on_demand_mode else local_wildcard_dict

                # Special case: __*/name__ should match both 'name' and 'name/*' at any depth
                if keyword.startswith('*/') and len(keyword) > 2:
                    base_name = keyword[2:]  # Remove '*/' prefix

                    logging.debug(f"[wild-card] [get_wildcard_options] Pattern: keyword={keyword}, base={base_name}, on_demand={_on_demand_mode}, search_dict_size={len(search_dict)}")

                    matched_count = 0
                    for k in search_dict.keys():
                        # Match if key ends with base_name or contains base_name/subdirs
                        # Pattern matching examples for base_name="dragon":
                        #   "dragon" -> match (exact)
                        #   "fantasy/dragon" -> match (nested file)
                        #   "dragon/fire" -> match (subfolder)
                        #   "fantasy/dragon/fire" -> match (deeply nested)
                        if (k == base_name or
                            k.endswith('/' + base_name) or
                            k.startswith(base_name + '/') or
                            ('/' + base_name + '/') in k):
                            logging.debug(f"[wild-card] [get_wildcard_options] Matched: {k}")
                            v = get_wildcard_value(k)
                            if v:
                                total_patterns += v
                                found = True
                                matched_count += 1

                    logging.debug(f"[wild-card] [get_wildcard_options] Result: matched={matched_count}, patterns={len(total_patterns)}")
                else:
                    # General wildcard pattern matching
                    subpattern = keyword.replace('*', '.*').replace('+', '\\+')
                    for k in search_dict.keys():
                        if re.match(subpattern, k) is not None or re.match(subpattern, k+'/') is not None:
                            # Load on-demand if needed
                            v = get_wildcard_value(k)
                            if v:
                                total_patterns += v
                                found = True

                if found:
                    options.extend(total_patterns)
            # Note: Fallback to __*/name__ is handled in replace_wildcard, not here

        return options

    def replace_wildcard(string):
        pattern = r"__([\w.\-+/*\\]+?)__"
        matches = re.findall(pattern, string)

        replacements_found = False

        for match in matches:
            keyword = match.lower()
            keyword = wildcard_normalize(keyword)

            # Use get_wildcard_value for on-demand loading support
            options = get_wildcard_value(keyword)

            if options is not None:
                # look for adjusted probability
                adjusted_probabilities = []
                total_prob = 0
                for option in options:
                    parts = option.split('::', 1)
                    if len(parts) == 2 and is_numeric_string(parts[0].strip()):
                        config_value = float(parts[0].strip())
                    else:
                        config_value = 1  # Default value if no configuration is provided

                    adjusted_probabilities.append(config_value)
                    total_prob += config_value

                normalized_probabilities = [prob / total_prob for prob in adjusted_probabilities]
                selected_item = random_gen.choice(options, p=normalized_probabilities, replace=False)
                replacement = re.sub(r'^\s*[0-9.]+::', '', selected_item, count=1)
                replacements_found = True
                string = string.replace(f"__{match}__", replacement, 1)
            elif '*' in keyword:
                total_patterns = []
                found = False

                # For wildcard patterns, search through available wildcards
                search_dict = available_wildcards if _on_demand_mode else local_wildcard_dict

                # Special case: __*/name__ should match both 'name' and 'name/*' at any depth
                if keyword.startswith('*/') and len(keyword) > 2:
                    base_name = keyword[2:]  # Remove '*/' prefix

                    for k in search_dict.keys():
                        # Match if key ends with base_name or contains base_name/subdirs
                        # Pattern matching examples for base_name="dragon":
                        #   "dragon" -> match (exact)
                        #   "fantasy/dragon" -> match (nested file)
                        #   "dragon/fire" -> match (subfolder)
                        #   "fantasy/dragon/fire" -> match (deeply nested)
                        if (k == base_name or
                            k.endswith('/' + base_name) or
                            k.startswith(base_name + '/') or
                            ('/' + base_name + '/') in k):
                            v = get_wildcard_value(k)
                            if v:
                                total_patterns += v
                                found = True
                else:
                    # General wildcard pattern matching
                    subpattern = keyword.replace('*', '.*').replace('+', '\\+')
                    for k in search_dict.keys():
                        if re.match(subpattern, k) is not None or re.match(subpattern, k+'/') is not None:
                            # Load on-demand if needed
                            v = get_wildcard_value(k)
                            if v:
                                total_patterns += v
                                found = True

                if found:
                    replacement = random_gen.choice(total_patterns)
                    replacements_found = True
                    string = string.replace(f"__{match}__", replacement, 1)
            elif '/' not in keyword:
                string_fallback = string.replace(f"__{match}__", f"__*/{match}__", 1)
                string, replacements_found = replace_wildcard(string_fallback)

        return string, replacements_found

    replace_depth = 100
    stop_unwrap = False
    while not stop_unwrap and replace_depth > 1:
        replace_depth -= 1  # prevent infinite loop

        option_quantifier = [e.groupdict() for e in RE_WildCardQuantifier.finditer(text)]
        for match in option_quantifier:
            keyword = match['keyword'].lower()
            quantifier = int(match['quantifier']) if match['quantifier'] else 1
            replacement = '__|__'.join([keyword,] * quantifier)
            wilder_keyword = keyword.replace('*', '\\*')
            RE_TEMP = re.compile(fr"(?P<quantifier>\d+)#__(?P<keyword>{wilder_keyword})__", re.IGNORECASE)
            text = RE_TEMP.sub(f"__{replacement}__", text)

        # pass1: replace options
        pass1, is_replaced1 = replace_options(text)

        while is_replaced1:
            pass1, is_replaced1 = replace_options(pass1)

        # pass2: replace wildcards
        text, is_replaced2 = replace_wildcard(pass1)
        stop_unwrap = not is_replaced1 and not is_replaced2

    return text


def is_numeric_string(input_str):
    return re.match(r'^-?(\d*\.?\d+|\d+\.?\d*)$', input_str) is not None


def expand(text, seed):
    refresh_wildcards()
    with _lock:
        return process(text, seed)
