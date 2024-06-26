#!/bin/bash

{{% for path in FILEPATH %}}
    {{% if MISSING_FILE_PASS %}}
{{% if path.endswith("/") %}}
{{% if FILE_REGEX %}}
        echo "Create specific tests for this rule because of regex"
{{% else %}}
rm -rf {{{ path }}}
{{% endif %}}
{{% else %}}
        rm -f {{{ path }}}
{{% endif %}}
    {{% else %}}
        {{% if path.endswith("/") %}}
if [ ! -d {{{ path }}} ]; then
    mkdir -p {{{ path }}}
fi
{{% if FILE_REGEX %}}
        echo "Create specific tests for this rule because of regex"
        {{% elif RECURSIVE %}}
        find -L {{{ path }}} -type d -exec chgrp {{{ GID_OR_NAME }}} {} \;
{{% else %}}
        chgrp {{{ GID_OR_NAME }}} {{{ path }}}
{{% endif %}}
        {{% else %}}
        if [ ! -f {{{ path }}} ]; then
            mkdir -p "$(dirname '{{{ path }}}')"
            touch {{{ path }}}
        fi
        chgrp {{{ GID_OR_NAME }}} {{{ path }}}
        {{% endif %}}
    {{% endif %}}
{{% endfor %}}
