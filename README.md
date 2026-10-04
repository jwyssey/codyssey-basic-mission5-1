# Mini Redis

Python 3.8 이상에서 실행하는 학습용 인메모리 키·값 저장소입니다. 해시맵(체이닝), 이중 연결 리스트(LRU), 최소 힙(TTL)을 직접 구현했습니다. 외부 패키지는 필요하지 않습니다.

```bash
python -m mini_redis.main
```

```text
mini-redis> SET name "Alice Kim"
OK
mini-redis> GET name
"Alice Kim"
mini-redis> EXPIRE name 30
(integer) 1
mini-redis> TTL name
(integer) 30
mini-redis> INFO memory
used_memory:13
maxmemory:0
evicted_keys:0
mini-redis> quit
```

지원 명령은 `SET key value`, `GET key`, `DEL key`, `EXISTS key`, `DBSIZE`, `KEYS`, `CONFIG SET maxmemory bytes`, `INFO memory`, `EXPIRE key seconds`, `TTL key`입니다. 명령어는 대소문자를 구분하지 않으며, 공백이 있는 키나 값은 큰따옴표로 감쌀 수 있습니다.

`maxmemory`의 단위는 바이트이며 0은 무제한입니다. `used_memory`는 키와 값의 UTF-8 바이트 수만 합산합니다. 메모리 제한을 낮추면 즉시 오래 사용하지 않은 키부터 제거합니다. 단일 키와 값이 제한보다 크면 `SET`은 OOM 오류를 내고 기존 데이터는 유지합니다. `TTL`은 남은 초를 올림하여 표시합니다.

평가 질문은 [EVALUATION.md](EVALUATION.md)에 있습니다.
