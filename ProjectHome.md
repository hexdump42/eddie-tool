The Eddie Tool can perform all basic system monitoring checks, such as:
  * filesystem;
  * processes;
  * system load;
  * network configuration.

It can also perform such network monitoring tasks as:
  * ping checks;
  * HTTP checks;
  * POP3 tests;
  * SNMP queries;
  * RADIUS authentication tests;
  * customized TCP port checks.

Finally, a few checks lend themselves to security monitoring:
  * watching files for changes;
  * scanning logfiles.

The Eddie Tool can also send any collected statistic to RRD files to be displayed graphically by any standard RRD tool. No need to run multiple monitoring and data collection agents. Monitoring rules are just like Python expressions and can be as simple or as complex as needed. Advanced alert control functionality such as exponential back-off and dependencies are also standard.