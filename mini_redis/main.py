"""Mini Redis 명령 파싱과 대화형 프롬프트."""

import json
import shlex

from .store import MiniRedis


INTEGER_ERROR = "(error) ERR value is not an integer or out of range"
OOM_ERROR = "(error) OOM command not allowed when used_memory > 'maxmemory'"


def _integer(text):
    """Redis 스타일의 부호 있는 64비트 정수를 읽는다."""
    try:
        value = int(text, 10)
    except ValueError:
        return None
    if not -(1 << 63) <= value < (1 << 63):
        return None
    return value


def _number(value):
    return "(integer) {}".format(value)


def _wrong_arguments(command):
    return "(error) ERR wrong number of arguments for '{}' command".format(command)


def execute(store, line):
    """한 줄을 파싱하고 결과 문자열을 돌려준다. 빈 줄은 None이다."""
    try:
        lexer = shlex.shlex(line, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        lexer.quotes = '"'  # 공백 없는 작은따옴표는 값의 일부로 취급한다.
        words = list(lexer)
    except ValueError:
        return "(error) ERR invalid quoted string"
    if not words:
        return None

    command = words[0].upper()
    args = words[1:]
    if command in ("EXIT", "QUIT"):
        return "__EXIT__" if not args else _wrong_arguments(command)

    if command in ("DBSIZE", "KEYS"):
        expected = 0
    elif command in ("GET", "DEL", "EXISTS", "TTL"):
        expected = 1
    elif command in ("SET", "EXPIRE"):
        expected = 2
    else:
        expected = None
    if expected is not None and len(args) != expected:
        return _wrong_arguments(command)

    if command == "SET":
        return "OK" if store.set(args[0], args[1]) else OOM_ERROR
    if command == "GET":
        value = store.get(args[0])
        return "(nil)" if value is None else json.dumps(value, ensure_ascii=False)
    if command == "DEL":
        return _number(store.delete(args[0]))
    if command == "EXISTS":
        return _number(store.exists(args[0]))
    if command == "DBSIZE":
        return _number(store.dbsize())
    if command == "KEYS":
        keys = store.keys()
        if not keys:
            return "(empty array)"
        return "\n".join(
            "{}. {}".format(index, json.dumps(key, ensure_ascii=False))
            for index, key in enumerate(keys, 1)
        )
    if command == "CONFIG":
        if len(args) != 3:
            return _wrong_arguments(command)
        if args[0].upper() != "SET" or args[1].lower() != "maxmemory":
            return "(error) ERR unsupported CONFIG option"
        limit = _integer(args[2])
        if limit is None or limit < 0:
            return INTEGER_ERROR
        store.config_set_maxmemory(limit)
        return "OK"
    if command == "INFO":
        if len(args) != 1:
            return _wrong_arguments(command)
        if args[0].lower() != "memory":
            return "(error) ERR unsupported INFO section"
        return store.info_memory()
    if command == "EXPIRE":
        seconds = _integer(args[1])
        return INTEGER_ERROR if seconds is None else _number(store.expire(args[0], seconds))
    if command == "TTL":
        return _number(store.ttl(args[0]))
    return "(error) ERR unknown command '{}'".format(words[0])


def main():
    """EOF, exit, quit까지 명령을 반복해서 읽는다."""
    store = MiniRedis()
    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        result = execute(store, line)
        if result == "__EXIT__":
            break
        if result is not None:
            print(result)


if __name__ == "__main__":
    main()
