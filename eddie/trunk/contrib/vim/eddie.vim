" Vim syn file
" Language:	Eddie Config
" Maintainer:	Dougal Scott <dwagon@pobox.com>
"
:syn keyword eddieType MSG PROC PID SP METASTAT STORE IPF FILE COM LOGSCAN
:syn keyword eddieType SYS IOSTAT CPU NIC IF PID group CLASS ALIAS PORT
:syn keyword eddieType SMTP POP3TIMING RADIUS PING SNMP HTTP FS NET DISK
:syn keyword eddieType TAPE
:highlight link eddieType Type

:syn keyword eddieConfig LOGFILE LOGLEVEL ADMIN ADMINLEVEL ADMIN_NOTIFY
:syn keyword eddieConfig NUMTHREADS SCANPERIOD CONSOLE_PORT EMAIL_FROM
:syn keyword eddieConfig EMAIL_REPLYTO ELVINURL ELVINSCOPE INTERPRETERS
:syn keyword eddieConfig INCLUDE WORKDIR SENDMAIL RESCANCONFIGS
:highlight link eddieConfig Type

:syn match eddieStatement +rule=+
:syn match eddieStatement +scanperiod=+
:syn match eddieStatement +server=+
:syn match eddieStatement +community=+
:syn match eddieStatement +user=+
:syn match eddieStatement +password=+
:syn match eddieStatement +nic=+
:syn match eddieStatement +secret=+
:syn match eddieStatement +action=+
:syn match eddieStatement +actelse=+
:syn match eddieStatement +act2ok=+
:syn match eddieStatement +checkwait=+
:syn match eddieStatement +numchecks=+
:syn match eddieStatement +name=+
:syn match eddieStatement +drive=+
:syn match eddieStatement +oid=+
:syn match eddieStatement +host=+
:syn match eddieStatement +port=+
:syn match eddieStatement +send=+
:syn match eddieStatement +expect=+
:syn match eddieStatement +protocol=+
:syn match eddieStatement +bindaddr=+
:syn match eddieStatement +cpu=+
:syn match eddieStatement +notifyperiod=+
:syn match eddieStatement +escalperiod=+
:syn match eddieStatement +template=+
:syn match eddieStatement +pidfile=+
:syn match eddieStatement +cmd=+
:syn match eddieStatement +file=+
:syn match eddieStatement +regex=+
:syn match eddieStatement +regfile=+
:syn match eddieStatement +fs=+
:syn match eddieStatement +console=+
:syn match eddieStatement +request_timeout=+
:syn match eddieStatement +history=+
:syn match eddieStatement +checkdependson=+
:syn match eddieStatement +disabled=+
:syn match eddieStatement +actionperiod=+
:syn match eddieStatement +actionmaxcalls=+
:syn match eddieStatement +checktime=+
:syn match eddieStatement +excludehosts=+
:highlight link eddieStatement Statement

:syn keyword eddieAction email ticker netsaint elvinrrd system restart elvindb log
:highlight link eddieAction PreProc

:syn match eddieComment /#.*/
:highlight link eddieComment Comment

:syn match eddieVariable /%([^)]*)./ contained
:highlight link eddieVariable Identifier

:syn region eddieString start=+'+ end=+'+ skip=+\\'+ contains=eddieVariable
:syn region eddieString start=+"+ end=+"+ skip=+\\"+ contains=eddieVariable
:highlight link eddieString String
