# SPDX-FileCopyrightText: 2024 IObundle
#
# SPDX-License-Identifier: MIT

import os


def setup(py_params_dict):
    VERSION = "0.1"
    BOOTROM_ADDR_W = (
        py_params_dict["bootrom_addr_w"] if "bootrom_addr_w" in py_params_dict else 12
    )

    attributes_dict = {
        "version": VERSION,
        "confs": [
            {
                "name": "DATA_W",
                "descr": "Data bus width",
                "type": "F",
                "val": "32",
                "min": "0",
                "max": "32",
            },
            {
                "name": "ADDR_W",
                "descr": "Address bus width",
                "type": "F",
                "val": BOOTROM_ADDR_W - 2,
                "min": "0",
                "max": "32",
            },
        ],
        #
        # Ports
        #
        "ports": [
            {
                "name": "clk_en_rst_s",
                "descr": "Clock and reset",
                "signals": {
                    "type": "clk_en_rst",
                },
            },
            {
                "name": "cbus_s",
                "descr": "Front-end control interface",
                "signals": {
                    "type": "axi",
                    "prefix": "cbus_",
                    # BOOTROM_ADDR_W + 1 for remaining csrs ("VERSION" csr)
                    "ADDR_W": BOOTROM_ADDR_W - 2 + 1,
                    "DATA_W": "DATA_W",
                },
            },
            {
                "name": "ext_rom_bus_io",
                "descr": "External ROM signals",
                "signals": [
                    {
                        "name": "ext_rom_en_o",
                        "width": "1",
                    },
                    {
                        "name": "ext_rom_addr_o",
                        "width": BOOTROM_ADDR_W - 2,
                    },
                    {
                        "name": "ext_rom_rdata_i",
                        "width": "DATA_W",
                    },
                ],
            },
        ],
        #
        # Wires
        #
        "wires": [
            {
                "name": "rom",
                "descr": "'rom' register interface",
                "signals": [
                    {"name": "rom_raddr_rd", "width": BOOTROM_ADDR_W - 2},
                    {"name": "rom_rdata_rd", "width": "DATA_W"},
                    {"name": "rom_rvalid_rd", "width": 1},
                    {"name": "rom_ren_rd", "width": 1},
                    {"name": "rom_rready_rd", "width": 1},
                ],
            },
            {
                "name": "rom_rvalid_data_i",
                "descr": "Register input",
                "signals": [
                    {"name": "rom_ren_rd"},
                ],
            },
            {
                "name": "rom_rvalid_data_o",
                "descr": "Register output",
                "signals": [
                    {"name": "rom_rvalid_rd"},
                ],
            },
        ],
        #
        # Blocks
        #
        "subblocks": [
            {
                "core_name": "iob_csrs",
                "instance_name": "csrs_inst",
                "version": VERSION,
                "csrs": [
                    {
                        "name": "rom",
                        "descr": "ROM access.",
                        "regs": [
                            {
                                "name": "rom",
                                "descr": "Bootloader ROM (read).",
                                "type": "R",
                                "n_bits": "DATA_W",
                                "rst_val": 0,
                                "addr": -1,
                                "log2n_items": BOOTROM_ADDR_W - 2,
                                "autoreg": False,
                            },
                        ],
                    }
                ],
                "csr_if": "axi",
                "connect": {
                    "clk_en_rst_s": "clk_en_rst_s",
                    "control_if_s": "cbus_s",
                    # Register interfaces
                    "rom_io": "rom",
                },
            },
            {
                "core_name": "iob_reg",
                "instance_name": "rom_rvalid_r",
                "instance_description": "ROM rvalid register",
                "parameters": {
                    "DATA_W": 1,
                    "RST_VAL": "1'b0",
                },
                "connect": {
                    "clk_en_rst_s": "clk_en_rst_s",
                    "data_i": "rom_rvalid_data_i",
                    "data_o": "rom_rvalid_data_o",
                },
            },
        ],
        #
        # Snippets
        #
        "snippets": [
            {
                "verilog_code": """
   assign ext_rom_en_o   = rom_ren_rd;
   assign ext_rom_addr_o = rom_raddr_rd;
   assign rom_rdata_rd   = ext_rom_rdata_i;
   assign rom_rready_rd  = 1'b1;  // ROM is always ready
""",
            },
        ],
    }

    copy_sw_srcs_with_rename(py_params_dict)

    return attributes_dict


def copy_sw_srcs_with_rename(py_params):
    """Copy software sources, and rename them based on correct SoC name."""
    SOC_NAME = py_params.get("soc_name", "iob_system")

    # Don't create files for other targets (like clean)
    if py_params.get("py2hwsw_target") != "setup":
        return

    SRC_DIR = os.path.join(os.path.dirname(__file__), "software_templates/src")
    DEST_DIR = os.path.join(py_params.get("build_dir"), "software/src")
    os.makedirs(DEST_DIR, exist_ok=True)

    for filename in os.listdir(SRC_DIR):
        new_filename = filename.replace("iob_system", SOC_NAME)
        src = os.path.join(SRC_DIR, filename)
        dst = os.path.join(DEST_DIR, new_filename)

        # Read file, replace strings with SoC name, and write new file
        with open(src, "r") as file:
            lines = file.readlines()
        for idx in range(len(lines)):
            lines[idx] = (
                lines[idx]
                .replace("iob_system", SOC_NAME)
                .replace("iob_system".upper(), SOC_NAME.upper())
            )
        with open(dst, "w") as file:
            file.writelines(lines)
