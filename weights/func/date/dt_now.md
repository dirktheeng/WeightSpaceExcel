# dt_now (id 349): NOW and TODAY

Hand-written (log/func-date-agent.md). Phases: PC 0 io 4 (clock), PC 1 read CLOCK (0x301000 = 3149824), PC 2 compute and return. T0 = 0 NOW, 1 TODAY. NOW = 25569 + secs fl(1/86400) (Unix epoch is serial 25569); TODAY = 25569 + FLOOR(secs/86400 + 1e-9), the 1e-9 day guard keeping an exact midnight from flooring to the previous day after rounding of the product.

**Limits.** UTC only: Excel uses local time, and no time zone word exists (requested in the log). Volatility is a FUNC_TABLE flag for the evaluator (memory-map FUNC_TABLE word 0x800 + fid), not something this network sets.

**Parameters.** 180 dense parameters, 42 layers. **Tests.** test_dt_now.py (PC 1 entry with a test-placed clock word, plus a live range check).
