#!/usr/bin/env python
# -*- coding: utf-8 -*-
from akshare.stock_feature.stock_cyq_em import stock_cyq_em
df = stock_cyq_em(symbol='601628', adjust='')
df_sorted = df.sort_values(by='日期', ascending=False)
print(df_sorted.to_string())
