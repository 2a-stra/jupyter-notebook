#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import re
import numpy as np
from matplotlib import pyplot as plt


# 1. Market trades log "market_logs":
# 
# trade timestamp in nanoseconds
# 
# side:
# 
# -1 sell
# 
# +1 buy
# 
# price
# volume
# 
# book state:
# volume_bid@bid_price x ask_price@volume_ask

# In[2]:


market_df = pd.read_csv("market_logs.log", header=None)
market_df.shape


# In[3]:


print("\n".join(market_df.loc[0,:]))


# In[4]:


def tm(src: str) -> int:
    '''parse timestamp'''
    res = re.findall("at (\d+) with", src)[0]
    return int(res)


# In[5]:


def side(src: str) -> int:
    res = re.findall("side (.+)$", src)[0]
    return int(res)


# In[6]:


def price(src: str) -> float:
    res = re.findall("price (.+)$", src)[0]
    return float(res)


# In[7]:


market_df.columns = ["time_src", "price_src", "volume_src"]
market_df["ts"] = market_df["time_src"].apply(tm)
market_df["side"] = market_df["time_src"].apply(side)
market_df.drop("time_src", axis=1, inplace=True)


# In[8]:


market_df["price"] = market_df["price_src"].apply(price)
market_df.drop("price_src", axis=1, inplace=True)


# In[9]:


def bid_price(src: str) -> float:
    res = re.findall("@(.+)x", src)[0]
    return float(res)


# In[10]:


def ask_price(src: str) -> float:
    res = re.findall("x(.+)@", src)[0]
    return float(res)


# In[11]:


market_df["bid_price"] = market_df["volume_src"].apply(bid_price)
market_df["ask_price"] = market_df["volume_src"].apply(ask_price)
market_df.drop("volume_src", axis=1, inplace=True)


# In[12]:


# middle price
market_df["mid_price"] = (market_df["ask_price"] + market_df["bid_price"]) / 2


# In[13]:


market_df.set_index("ts", inplace=True)
market_df


# 2. Trade execution log: "exec_logs"
# 
# side - {+1 - order executer on bid (our buy trade), -1 - order executed on ask (our sell trade)}
# 
# price
# 
# traded volume
# 
# volume_left
# 
# delta_execsend - time between sending limit order and its executin

# In[14]:


exec_df = pd.read_csv("exec_logs.log", header=None)
exec_df.columns = ["time_src", "side_src", "price_src", "trade_vol_src", "left_vol_src", "delta_src"]


# In[15]:


exec_df["ts"] = exec_df["time_src"].apply(tm)
exec_df["side"] = exec_df["side_src"].apply(lambda st: int(st.strip().split(" ")[1]))
exec_df["price"] = exec_df["price_src"].apply(price)
exec_df["delta"] = exec_df["delta_src"].apply(lambda st: int(st.strip().split(" ")[1]))
exec_df.drop(["time_src", "side_src", "price_src", "delta_src"], axis=1, inplace=True)
exec_df.drop(["trade_vol_src", "left_vol_src"], axis=1, inplace=True)
#exec_df.set_index("ts", inplace=True)
exec_df


# In[16]:


# adding 5 seconds to timestamp
exec_df["plus_5s"] = exec_df["ts"] + 5_000_000_000  # nanoseconds


# In[17]:


indx_ts = market_df.index.to_list()

def find_ts(exec_ts: int) -> int:
    '''return market price timestamp at least 5 sec after trade execution'''
    global indx_ts
    for indx in indx_ts:
        if indx >= exec_ts:
            #print(indx)
            return indx


# In[18]:


exec_df["market5s"] = exec_df["plus_5s"].apply(find_ts)


# In[19]:


# get mid_price after 5 sec
exec_df["mid_price"] = exec_df["market5s"].apply(lambda x: market_df.loc[x, "mid_price"])


# Trade quality estimation:
# dmid5 = ( mid_price_after_5_seconds - our_trade_price ) * trade_direction_side

# In[20]:


# trade estimation after 5 sec
exec_df["dmid5"] = (exec_df["mid_price"] - exec_df["price"]) * exec_df["side"]
exec_df


# In[21]:


# total result
exec_df["dmid5"].sum()


# In[22]:


exec_df["dmid5"].describe()


# In[23]:


plt.plot(exec_df["dmid5"])


# In[24]:


exec_df["delta"].describe()


# In[25]:


plt.plot(exec_df["delta"] / 1_000_000_000)  # seconds


# What is the correlation between `dmid5` and delta_execsend?

# In[26]:


# correlation between trade estimation and time delta
plt.scatter(exec_df["dmid5"], exec_df["delta"])


# In[27]:


corr = np.corrcoef(exec_df["dmid5"], exec_df["delta"])
print("Correlation: ", corr[0,1])


# => No correlation between trade quality estimation `dmid5` and execution send time delta
