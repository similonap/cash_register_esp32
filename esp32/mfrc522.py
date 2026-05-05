"""
mfrc522.py — MicroPython driver for the MFRC522 NFC/RFID reader (SPI)
"""

from time import sleep_ms

class MFRC522:
    # Commands
    PCD_IDLE       = 0x00
    PCD_AUTHENT    = 0x0E
    PCD_TRANSCEIVE = 0x0C
    PCD_RESETPHASE = 0x0F

    # PICC commands
    REQIDL  = 0x26
    REQALL  = 0x52

    # Status
    OK       = 0
    NOTAGERR = 1
    ERR      = 2

    # Registers
    CommandReg     = 0x01
    CommIEnReg     = 0x02
    CommIrqReg     = 0x04
    ErrorReg       = 0x06
    FIFODataReg    = 0x09
    FIFOLevelReg   = 0x0A
    ControlReg     = 0x0C
    BitFramingReg  = 0x0D
    ModeReg        = 0x11
    TxControlReg   = 0x14
    TxAutoReg      = 0x15
    TModeReg       = 0x2A
    TPrescalerReg  = 0x2B
    TReloadRegH    = 0x2C
    TReloadRegL    = 0x2D

    MAX_LEN = 16

    def __init__(self, spi, cs, rst=None):
        self.spi = spi
        self.cs = cs
        self.rst = rst
        self.cs.value(1)
        if self.rst:
            self.rst.value(0)
            sleep_ms(50)
            self.rst.value(1)
            sleep_ms(50)
        self._init()

    def _write(self, addr, val):
        self.cs.value(0)
        self.spi.write(bytes([(addr << 1) & 0x7E, val & 0xFF]))
        self.cs.value(1)

    def _read(self, addr):
        self.cs.value(0)
        self.spi.write(bytes([((addr << 1) & 0x7E) | 0x80]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _set_bits(self, reg, mask):
        self._write(reg, self._read(reg) | mask)

    def _clear_bits(self, reg, mask):
        self._write(reg, self._read(reg) & ~mask)

    def _init(self):
        self._write(self.TModeReg, 0x8D)
        self._write(self.TPrescalerReg, 0x3E)
        self._write(self.TReloadRegL, 30)
        self._write(self.TReloadRegH, 0)
        self._write(self.TxAutoReg, 0x40)
        self._write(self.ModeReg, 0x3D)
        # antenna on
        if not (self._read(self.TxControlReg) & 0x03):
            self._set_bits(self.TxControlReg, 0x03)

    def _transceive(self, data):
        self._write(self.CommIEnReg, 0x77 | 0x80)
        self._clear_bits(self.CommIrqReg, 0x80)
        self._set_bits(self.FIFOLevelReg, 0x80)
        self._write(self.CommandReg, self.PCD_IDLE)
        for b in data:
            self._write(self.FIFODataReg, b)
        self._write(self.CommandReg, self.PCD_TRANSCEIVE)
        self._set_bits(self.BitFramingReg, 0x80)

        i = 2000
        while True:
            n = self._read(self.CommIrqReg)
            i -= 1
            if i == 0 or (n & 0x01) or (n & 0x30):
                break
        self._clear_bits(self.BitFramingReg, 0x80)

        if i == 0:
            return self.ERR, [], 0

        if self._read(self.ErrorReg) & 0x1B:
            return self.ERR, [], 0

        irq = self._read(self.CommIrqReg)
        if irq & 0x01:
            return self.NOTAGERR, [], 0

        back = []
        n = self._read(self.FIFOLevelReg)
        last_bits = self._read(self.ControlReg) & 0x07
        back_len = (n - 1) * 8 + last_bits if last_bits else n * 8
        n = max(1, min(n, self.MAX_LEN))
        for _ in range(n):
            back.append(self._read(self.FIFODataReg))

        return self.OK, back, back_len

    def request(self, req_mode):
        self._write(self.BitFramingReg, 0x07)
        status, _, back_bits = self._transceive([req_mode])
        if status != self.OK or back_bits != 0x10:
            return self.ERR, 0
        return self.OK, back_bits

    def anticoll(self):
        self._write(self.BitFramingReg, 0x00)
        status, back, _ = self._transceive([0x93, 0x20])
        if status == self.OK:
            if len(back) == 5:
                chk = 0
                for b in back[:4]:
                    chk ^= b
                if chk != back[4]:
                    return self.ERR, []
            else:
                return self.ERR, []
        return status, back
