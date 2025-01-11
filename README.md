![Logo](pysino.png)

# pysino
Simple TCP Client for Sinos MXPro in Python

Use on own Risk

Need: Pandas

```py

from pysino import TCP

client = TCP()

#Get Realtime Data
client.sub("DE000GG0UYM8")

#get Realtime Data as DataFrame
client.get("DE000GG0UYM8")

#Buy Order
client.make_order("DE000GG0UYM8", 10, "BUY")

#Sell Order
client.make_order("DE000GG0UYM8", 10, "SELL")

client.close()

```

Have Fun!
