.. _adjust-vcs-server-mem:

VCSServer Memory Usage
----------------------

Starting from Version 4.18.X RhodeCode has a builtin memory monitor for gunicorn workers.
Enabling this can limit the maximum amount of memory system can use. Each worker
for VCS Server is monitored independently.
To enable Memory management make sure to have following settings inside `[app:main] section` of
:file:`home/{user}/.rccontrol/{instance-id}/vcsserver.ini` file.



    ; Maximum memory usage that each worker can use before it will receive a
    ; graceful restart signal 0 = memory monitoring is disabled
    ; Examples: 268435456 (256MB), 536870912 (512MB)
    ; 1073741824 (1GB), 2147483648 (2GB), 4294967296 (4GB)
    memory_max_usage = 1073741824

    ; How often in seconds to check for memory usage for each gunicorn worker
    memory_usage_check_interval = 60

    ; Threshold value for which we don't recycle worker if GarbageCollection
    ; frees up enough resources. Before each restart we try to run GC on worker
    ; in case we get enough free memory after that, restart will not happen.
    memory_usage_recovery_threshold = 0.8
