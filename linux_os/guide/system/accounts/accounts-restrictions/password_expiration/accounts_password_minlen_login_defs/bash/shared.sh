# platform = Red Hat Virtualization 4,multi_platform_fedora,multi_platform_ol,multi_platform_rhel,multi_platform_sle,multi_platform_almalinux

{{{ bash_instantiate_variables("var_accounts_password_minlen_login_defs") }}}
{{{ bash_replace_or_append(login_defs_path, '^PASS_MIN_LEN', "$var_accounts_password_minlen_login_defs", '%s %s', cce_identifiers=cce_identifiers) }}}
