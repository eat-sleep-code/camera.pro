#!/usr/bin/env python3
"""
ft5506_touch.py — Userspace touch driver for FT5506 capacitive touchscreen.

The FT5506 INT pin is not wired on this display, so the kernel's edt_ft5x06
driver never receives an interrupt and its polling path silently produces no
events.  This daemon reads the FT5506 directly over I2C and injects
multi-touch events via uinput, which Qt's evdevtouch plugin picks up normally.

Run as root (required for uinput and i2c access):
    sudo python3 ft5506_touch.py

Or via the systemd service installed by install.sh.
"""

import os
import sys
import time
import struct
import smbus
from evdev import UInput, AbsInfo, ecodes as e

# ---------------------------------------------------------------------------
# Configuration

I2C_BUS      = 10       # i2c-10 (i2c0mux → sub-bus)
FT5506_ADDR  = 0x38
POLL_HZ      = 60       # polling rate
SCREEN_W     = 800
SCREEN_H     = 480
MAX_TOUCHES  = 5

# The DT node has touchscreen-inverted-x and touchscreen-inverted-y set.
INVERT_X     = True
INVERT_Y     = True

# ---------------------------------------------------------------------------
# FT5x06 register map

REG_NUM_TOUCHES = 0x02   # number of active touch points (lower nibble)
REG_TOUCH_BASE  = 0x03   # 6 bytes per touch: XH XL YH YL WEIGHT AREA

# Event flags in XH bits[7:6]
EVT_PRESS   = 0
EVT_RELEASE = 1
EVT_CONTACT = 2


def read_touches(bus):
    """Return list of (tracking_id, x, y, event_flag) tuples."""
    try:
        count = bus.read_byte_data(FT5506_ADDR, REG_NUM_TOUCHES) & 0x0F
        if count == 0 or count > MAX_TOUCHES:
            return []
        touches = []
        for i in range(count):
            base = REG_TOUCH_BASE + i * 6
            d = bus.read_i2c_block_data(FT5506_ADDR, base, 6)
            evt  = (d[0] >> 6) & 0x03
            x    = ((d[0] & 0x0F) << 8) | d[1]
            tid  = (d[2] >> 4) & 0x0F
            y    = ((d[2] & 0x0F) << 8) | d[3]
            if INVERT_X:
                x = SCREEN_W - 1 - x
            if INVERT_Y:
                y = SCREEN_H - 1 - y
            touches.append((tid, x, y, evt))
        return touches
    except OSError:
        return []


def make_uinput():
    caps = {
        e.EV_KEY: [e.BTN_TOUCH, e.BTN_LEFT],
        e.EV_ABS: [
            (e.ABS_X,               AbsInfo(0, 0, SCREEN_W - 1, 4, 0, 0)),
            (e.ABS_Y,               AbsInfo(0, 0, SCREEN_H - 1, 4, 0, 0)),
            (e.ABS_MT_SLOT,         AbsInfo(0, 0, MAX_TOUCHES - 1, 0, 0, 0)),
            (e.ABS_MT_TRACKING_ID,  AbsInfo(0, -1, 65535, 0, 0, 0)),
            (e.ABS_MT_POSITION_X,   AbsInfo(0, 0, SCREEN_W - 1, 4, 0, 0)),
            (e.ABS_MT_POSITION_Y,   AbsInfo(0, 0, SCREEN_H - 1, 4, 0, 0)),
            (e.ABS_MT_TOUCH_MAJOR,  AbsInfo(0, 0, 255, 0, 0, 0)),
        ],
    }
    return UInput(caps, name='ft5506-touchscreen', version=0x0100)


def main():
    bus = smbus.SMBus(I2C_BUS)
    ui  = make_uinput()

    print(f'ft5506_touch: polling FT5506 at i2c-{I2C_BUS}/0x{FT5506_ADDR:02x} '
          f'@ {POLL_HZ} Hz  →  {ui.device.path}', flush=True)

    interval     = 1.0 / POLL_HZ
    slot_state   = {}   # slot → tracking_id currently reported
    was_touching = False

    try:
        while True:
            t0      = time.monotonic()
            touches = read_touches(bus)

            # Build slot → (x, y) map for active touches
            active = {}
            for tid, x, y, evt in touches:
                slot = tid % MAX_TOUCHES
                active[slot] = (tid, x, y)

            # Close slots that are no longer active
            for slot in list(slot_state):
                if slot not in active:
                    ui.write(e.EV_ABS, e.ABS_MT_SLOT,        slot)
                    ui.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, -1)
                    del slot_state[slot]

            # Report active slots
            for slot, (tid, x, y) in active.items():
                ui.write(e.EV_ABS, e.ABS_MT_SLOT,        slot)
                if slot_state.get(slot) != tid:
                    ui.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, tid)
                    slot_state[slot] = tid
                ui.write(e.EV_ABS, e.ABS_MT_POSITION_X,  x)
                ui.write(e.EV_ABS, e.ABS_MT_POSITION_Y,  y)

            # Single-touch compatibility (ABS_X/Y + BTN_TOUCH)
            touching = bool(active)
            if active:
                first = next(iter(active.values()))
                ui.write(e.EV_ABS, e.ABS_X, first[1])
                ui.write(e.EV_ABS, e.ABS_Y, first[2])
            if touching != was_touching:
                ui.write(e.EV_KEY, e.BTN_TOUCH, 1 if touching else 0)
                was_touching = touching

            ui.syn()

            elapsed = time.monotonic() - t0
            wait    = interval - elapsed
            if wait > 0:
                time.sleep(wait)

    except KeyboardInterrupt:
        pass
    finally:
        ui.close()
        bus.close()


if __name__ == '__main__':
    if os.geteuid() != 0:
        sys.exit('Must run as root (sudo)')
    main()
