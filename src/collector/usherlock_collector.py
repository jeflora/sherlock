#!/usr/bin/python3

import subprocess, argparse, os, time
import redis


MAX_LINES = 20000


def run_sysdig(
    sysdig_parameters, sysdig_filters, redis_host, redis_channel, port, window
):
    sysdig_proc = subprocess.Popen(
        ("sysdig", "-p", sysdig_parameters, sysdig_filters, "--unbuffered"),
        stdout=subprocess.PIPE,
    )

    if not sysdig_proc:
        return
    print(os.getpid(), flush=True)

    redis_pub = redis.StrictRedis(
        redis_host, port, charset="utf-8", decode_responses=True
    )

    lines = []
    start_time = time.time()
    for line in iter(sysdig_proc.stdout.readline, b""):
        lines.append(line.decode("utf-8"))
        if len(lines) % MAX_LINES == 0 or time.time() - start_time >= window:
            redis_pub.publish(redis_channel, "".join(lines))
            lines = []
            start_time = time.time()

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="uSherlockCollector",
        description="Collects system calls from the applications.",
    )
    parser.add_argument("sysdig_parameters")
    parser.add_argument("sysdig_filters")
    parser.add_argument("redis_host")
    parser.add_argument("redis_channel")
    parser.add_argument("-p", "--port", default=6379)
    parser.add_argument("-w", "--window", default=1, type=int)
    args = parser.parse_args()

    run_sysdig(
        args.sysdig_parameters,
        args.sysdig_filters,
        args.redis_host,
        args.redis_channel,
        args.port,
        args.window,
    )
