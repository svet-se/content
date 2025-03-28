#!/usr/bin/python3

"""
The build_sce.py script generates SCE (Script Check Engine) content that
supplements the standardized OVAL-based checks. This script generates
two major types of output artifacts:

   - <build>/<product>/checks/sce/metadata.json
   - <build>/<product>/checks/sce/<scripts>

The former is a map of information about all included SCE content in the
build system that is applicable for the specified product. It is used by
the shorthand generation to place SCE elements in the correct places. It
takes the following structure:

    rule_id -> struct {
        platforms: str/list  // What platforms the specified script applies to.
        check-import?: str/list in {stdout, stderr}, // Whether to preserve stdout or
                                                     // stderr (or both).
        check-export?: str/list of equals-separated values // List of env_var->xccdf_var mappings.
        complex-check?: str in {AND, OR} // Operator to use for combining SCE and OVAL
        filename: path under checks/sce that this script is in.
    }

Note that every SCE script must begin with a shebang, otherwise OpenSCAP
will fail to interpret (thinking it is XML)!
"""

from __future__ import print_function

import argparse

import ssg.build_sce
import ssg.environment
import ssg.templates
import ssg.products
from ssg.utils import mkdir_p


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--build-config-yaml", required=True,
        help="YAML file with information about the build configuration. "
        "e.g.: ~/scap-security-guide/build/build_config.yml"
    )
    p.add_argument(
        "--product-yaml", required=True,
        help="YAML file with information about the product we are building. "
        "e.g.: ~/scap-security-guide/rhel9/product.yml"
    )
    p.add_argument(
        "--templates-dir", required=True,
        help="Path to directory which contains content templates. "
        "e.g.: ~/scap-security-guide/shared/templates"
    )
    p.add_argument(
        "--output", required=True)
    args = p.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()

    # Create output directory if it doesn't yet exist.
    mkdir_p(args.output)

    env_yaml = ssg.environment.open_environment(
        args.build_config_yaml, args.product_yaml)
    empty = "/sce/empty/placeholder"
    product_yaml = ssg.products.Product(args.product_yaml)
    template_builder = ssg.templates.Builder(
        env_yaml, empty, args.templates_dir, empty, empty, empty, None)
    sce_builder = ssg.build_sce.SCEBuilder(
        env_yaml, product_yaml, template_builder, args.output)
    sce_builder.build()
