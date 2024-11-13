from datetime import datetime, timedelta

currentTime = datetime.now()
print(currentTime)
cur = (currentTime + timedelta(hours =0)).replace(minute=5, second=0, microsecond=0)
print(cur)
curTime = datetime()
print(curTime)
print( cur)
