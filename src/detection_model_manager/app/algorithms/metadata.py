STIDE = "stide"
BOSC = "bosc"


PARAMS_NEEDED = {
    STIDE: ["window"],
    BOSC: ["window"],
}

WINDOW_BASED_ALGOS = [
    STIDE,
    BOSC,
]


ALGOS_AVAILABLE = {
    STIDE: {
        "name": STIDE,
        "description": "The STIDE (Sequence Time-Delaying Embedding) algorithm uses a window sliding over a collection of system calls to define a baseline behavior database that will be used in the detection phase to find possible intrusions. Unlike BoSC, it maintains the original order of system calls.",
        "required_params": PARAMS_NEEDED[STIDE],
        "processing_technique": "timestamp_and_syscall",
        "index_map_name": "syscall_index_map",
    },
    BOSC: {
        "name": BOSC,
        "description": "The BoSC (Bags of System Calls) algorithm uses a sliding window over a collection of system calls to detect intrusions and define a baseline behavior database, which contains bags of system calls considered normal. The order in which the system calls are made is not taken into account because this algorithm counts the frequency of each system call every time it appears in the sliding window.",
        "required_params": PARAMS_NEEDED[BOSC],
        "processing_technique": "timestamp_and_syscall",
        "index_map_name": "syscall_index_map",
    },
}


def check_params_for_algorithm(name: str, params: dict) -> bool:
    if name not in ALGOS_AVAILABLE.keys():
        return False
    return all([param in params.keys() for param in PARAMS_NEEDED[name]])
