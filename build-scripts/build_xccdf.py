#!/usr/bin/python3

from __future__ import print_function

import argparse
import os
import os.path
from collections import namedtuple
import re

import ssg.build_yaml
import ssg.utils
import ssg.environment
import ssg.id_translate
import ssg.build_renumber
import ssg.products


Paths_ = namedtuple("Paths_", ["xccdf", "oval", "ocil", "build_ovals_dir"])


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converts SCAP Security Guide YAML benchmark data "
        "(benchmark, rules, groups) to XCCDF Shorthand Format"
    )
    parser.add_argument(
        "--build-config-yaml", required=True,
        help="YAML file with information about the build configuration. "
        "e.g.: ~/scap-security-guide/build/build_config.yml"
    )
    parser.add_argument(
        "--product-yaml", required=True,
        help="YAML file with information about the product we are building. "
        "e.g.: ~/scap-security-guide/rhel9/product.yml"
    )
    parser.add_argument(
        "--xccdf", required=True,
        help="Output XCCDF file. "
        "e.g.:  ~/scap-security-guide/build/rhel9/ssg-rhel9-xccdf.xml"
    )
    parser.add_argument(
        "--ocil", required=True,
        help="Output OCIL file. "
        "e.g.:  ~/scap-security-guide/build/rhel9/ssg-rhel9-ocil.xml"
    )
    parser.add_argument(
        "--oval", required=True,
        help="Output OVAL file. "
        "e.g.:  ~/scap-security-guide/build/rhel9/ssg-rhel9-oval.xml"
    )
    parser.add_argument(
        "--build-ovals-dir",
        dest="build_ovals_dir",
        help="Directory to store OVAL document for each rule.",
    )
    parser.add_argument(
        "--resolved-base",
        help="To which directory to put processed rule/group/value YAMLs."
    )
    parser.add_argument(
        "--thin-ds-components-dir",
        default="off",
        help="Directory to store XCCDF, OVAL, OCIL, for thin data stream. (off: to disable)"
        "e.g.: ~/scap-security-guide/build/rhel9/thin_ds_component/"
        "Fake profiles are used to create thin DS. Components are generated for each profile.",
    )
    return parser.parse_args()


def link_oval(xccdftree, checks, output_file_name, build_ovals_dir):
    translator = ssg.id_translate.IDTranslator("ssg")
    oval_linker = ssg.build_renumber.OVALFileLinker(
        translator, xccdftree, checks, output_file_name
    )
    oval_linker.build_ovals_dir = build_ovals_dir
    oval_linker.link()
    oval_linker.save_linked_tree()
    oval_linker.link_xccdf()
    return oval_linker


def link_ocil(xccdftree, checks, output_file_name, ocil):
    translator = ssg.id_translate.IDTranslator("ssg")
    ocil_linker = ssg.build_renumber.OCILFileLinker(
        translator, xccdftree, checks, output_file_name
    )
    ocil_linker.link(ocil)
    ocil_linker.save_linked_tree()
    ocil_linker.link_xccdf()


def store_xccdf_per_profile(loader, oval_linker, variables_ids, thin_ds_components_dir):
    for id_, xccdftree in loader.get_benchmark_xml_by_profile(variables_ids):
        xccdf_file_name = os.path.join(thin_ds_components_dir, "xccdf_{}.xml".format(id_))
        oval_file_name = os.path.join(thin_ds_components_dir, "oval_{}.xml".format(id_))

        checks = xccdftree.findall(".//{%s}check" % ssg.constants.XCCDF12_NS)
        oval_linker.linked_fname = oval_file_name
        oval_linker.linked_fname_basename = os.path.basename(oval_file_name)
        oval_linker.checks_related_to_us = oval_linker.get_related_checks(checks)

        oval_linker.link_xccdf()

        ssg.xml.ElementTree.ElementTree(xccdftree).write(xccdf_file_name, encoding="utf-8")


def get_linked_xccdf(loader, xccdftree, args):
    checks = xccdftree.findall(".//{%s}check" % ssg.constants.XCCDF12_NS)

    oval_linker = link_oval(xccdftree, checks, args.oval, args.build_ovals_dir)

    ocil = loader.export_ocil_to_xml()
    link_ocil(xccdftree, checks, args.ocil, ocil)
    return oval_linker, xccdftree


def get_variables_from_go_templating(rule, var_ids):
    go_templating_pattern = re.compile(r"{{(.*?)}}")
    go_templating_var_pattern = re.compile(r"\.([a-zA-Z0-9_]+)")
    for ele in rule.itertext():
        for match in go_templating_pattern.finditer(ele):
            for var in go_templating_var_pattern.finditer(match.group(1)):
                var_ids.add(var.group(1))


def get_rules_with_variables(xccdftree):
    rules = xccdftree.findall(".//{%s}Rule" % ssg.constants.XCCDF12_NS)
    out_var_ids = {}
    for rule in rules:
        var_ids = set()
        check_export_els = rule.findall(".//{%s}check-export" % ssg.constants.XCCDF12_NS)
        for check_export_el in check_export_els:
            var_ids.add(
                check_export_el.get("value-id").replace("xccdf_org.ssgproject.content_value_", "")
            )
        sub_els = rule.findall(".//{%s}sub" % ssg.constants.XCCDF12_NS)
        for sub_el in sub_els:
            var_ids.add(
                sub_el.get("idref").replace("xccdf_org.ssgproject.content_value_", "")
            )
        get_variables_from_go_templating(rule, var_ids)
        out_var_ids[
            rule.get("id").replace("xccdf_org.ssgproject.content_rule_", "")
        ] = var_ids
    return out_var_ids


def main():
    args = parse_args()

    env_yaml = ssg.environment.open_environment(
        args.build_config_yaml, args.product_yaml)
    product_yaml = ssg.products.Product(args.product_yaml)
    base_dir = product_yaml["product_dir"]
    benchmark_root = ssg.utils.required_key(env_yaml, "benchmark_root")

    # we have to "absolutize" the paths the right way, relative to the
    # product_yaml path
    if not os.path.isabs(benchmark_root):
        benchmark_root = os.path.join(base_dir, benchmark_root)

    loader = ssg.build_yaml.LinearLoader(
        env_yaml, args.resolved_base)
    loader.load_compiled_content()
    loader.load_benchmark(benchmark_root)
    loader.add_fixes_to_rules()

    _, xccdftree = get_linked_xccdf(loader, loader.get_benchmark_xml(), args)
    var_ids = get_rules_with_variables(xccdftree)

    build_thin_ds_for_each_rule = args.thin_ds_components_dir != "off"
    oval_linker, xccdftree = get_linked_xccdf(
        loader, loader.export_benchmark_to_xml(var_ids, build_thin_ds_for_each_rule), args
    )

    ssg.xml.ElementTree.ElementTree(xccdftree).write(
        args.xccdf, xml_declaration=True, encoding="utf-8")

    if build_thin_ds_for_each_rule:
        if not os.path.exists(args.thin_ds_components_dir):
            os.makedirs(args.thin_ds_components_dir)
        store_xccdf_per_profile(loader, oval_linker, var_ids, args.thin_ds_components_dir)
        oval_linker.build_ovals_dir = args.thin_ds_components_dir
        oval_linker.save_oval_document_for_each_xccdf_rule("oval_")


if __name__ == "__main__":
    main()
