from operator import index


def apply_filters(data_dicto: dict, user_filters: dict) -> bool:
    for filt_param, ufilters in user_filters.items():
        if data_dicto[filt_param] not in ufilters:
            return False
    return True


def data_to_dict(params: list, data: str) -> dict:
    data_tokens = data.split()

    # This function assumes that if "evt_args" exists
    #       is always at the end as if may result in several tokens
    # To work with "evt_args" in different places it would require a different logic
    if "evt_args" in params:
        if len(params) > len(data_tokens):
            # no args
            data_tokens.append("")
        elif len(params) < len(data_tokens):
            # more than one arg
            data_tokens[len(params) - 1] = " ".join(data_tokens[len(params) :])
            data_tokens = data_tokens[: len(params)]

    return dict(zip(params, data_tokens)) if len(params) == len(data_tokens) else None


def timestamp_and_syscall(data_dicto, index_map, cache, closing):
    if (
        not data_dicto
        or not index_map
        or closing
        or "evt_rawtime" not in data_dicto
        or "syscall_type" not in data_dicto
        or data_dicto["syscall_type"] not in index_map
    ):
        return None, cache
    return f"{data_dicto['evt_rawtime']} {index_map[data_dicto['syscall_type']]}", cache


def ml_50_syscalls_epoch(data_dicto, index_map, cache, closing):
    return "", None


def independent_replica_aggreg(data_dicto, index_map, cache, closing):
    return "", None


def events_total_order(data_dicto, index_map, cache, closing):
    return "", None


def periodic_interleaving(data_dicto, index_map, cache, closing):
    return "", None


PROCESSING_FUNCTIONS = {
    "timestamp_and_syscall": timestamp_and_syscall,
    "ml_50_syscalls_epoch": ml_50_syscalls_epoch,
    "independent_replica_aggreg": independent_replica_aggreg,
    "events_total_order": events_total_order,
    "periodic_interleaving": periodic_interleaving,
}
AVAILABLE_PROCESSING_FUNCTIONS = list(PROCESSING_FUNCTIONS.keys())


def process_data(
    func: str, params, user_filters, data, index_map, cache=None, closing=False
):
    if func not in AVAILABLE_PROCESSING_FUNCTIONS:
        return None, None

    if closing and (not data or data == "CLOSE"):
        return PROCESSING_FUNCTIONS[func](None, index_map, cache, closing)

    proc_lines = list()
    for data_dicto in [data_to_dict(params, line) for line in data.split("\n")]:
        if not data_dicto or not apply_filters(data_dicto, user_filters):
            continue
        proc_line, cache = PROCESSING_FUNCTIONS[func](
            data_dicto, index_map, cache, closing
        )
        if proc_line:
            proc_lines.append(proc_line)

    return "\n".join(proc_lines), cache
