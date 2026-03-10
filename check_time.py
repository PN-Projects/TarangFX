
import time
import datetime

msg_id = 7605518459812505601
msg_timestamp = msg_id >> 32
local_timestamp = int(time.time())
diff = msg_timestamp - local_timestamp

print(f"Message ID: {msg_id}")
print(f"Message Timestamp: {msg_timestamp} ({datetime.datetime.fromtimestamp(msg_timestamp)})")
print(f"Local Timestamp:   {local_timestamp} ({datetime.datetime.fromtimestamp(local_timestamp)})")
print(f"Difference: {diff} seconds")
