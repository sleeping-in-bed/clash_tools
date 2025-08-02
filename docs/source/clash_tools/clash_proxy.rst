`clash_proxy` - Environment Variables
=====================================

A shell script for setting up proxy environment variables in the current session.

**Usage**::

    eval "$(clash_proxy)"

**Description**:
  This script reads the configuration from ``config.yaml`` and sets up all necessary proxy environment variables for the current shell session.

**Environment Variables Set**:
  - ``http_proxy`` / ``HTTP_PROXY``
  - ``https_proxy`` / ``HTTPS_PROXY``
  - ``all_proxy`` / ``ALL_PROXY`` (SOCKS5)
  - ``no_proxy`` / ``NO_PROXY``

**Features**:
  - Automatic port detection from config file
  - Error handling and validation
  - Both lowercase and uppercase variable formats
  - Support for HTTP and SOCKS5 proxies

Permission Requirements
-----------------------

No special permissions required. Can be run by any user.

Troubleshooting
---------------

**Issue: clash_proxy Variables Not Set**

If environment variables aren't being set:

1. Make sure to use ``eval "$(clash_proxy)"`` or ``source clash_proxy`` (not just ``./clash_proxy``)
2. Check that ``config.yaml`` exists and contains valid port numbers
3. Verify the script has read permissions
