from misoc.interconnect.stream import Endpoint
from migen import *
from migen.genlib.fsm import FSM, NextState
from misoc.interconnect.csr_bus import Interface

# CSR Bus master

# Three interfaces
# CSR Port (master)
# Trans_init
#
# 
# 
# Trans_complete

CMD_REC = [('wr', 1), ('a', 14), ('d', 8)]
class CSR_Master(Module):
    def __init__(self, has_completion=True):
        self.cmd = Endpoint(CMD_REC)
        self.source = self.cmd

        if has_completion:
            self.completion = Endpoint(CMD_REC)
            self.sink = self.completion

        self.master = Interface()

        self.busy = Signal()

        self.comb += [ 
                self.cmd.ack.eq(0)
                ]

        samp_comp = Signal()

        if has_completion:
            self.sync += If(self.cmd.ack, 
                    self.completion.payload.a.eq(self.cmd.payload.a),
                    self.completion.payload.wr.eq(self.cmd.payload.wr),
                    If(self.cmd.payload.wr,
                        self.completion.payload.d.eq(self.master.dat_w))
                    )

            self.sync += If(samp_comp & ~self.completion.payload.wr,
                    self.completion.payload.d.eq(self.master.dat_r))


        fsm = FSM()
        fsm.act("IDLE",
                If(self.cmd.stb,
                    self.cmd.ack.eq(1),
                    self.master.we.eq(self.cmd.payload.wr),
                    self.master.adr.eq(self.cmd.payload.a),
                    self.master.dat_w.eq(self.cmd.payload.d),
                    NextState("READ")))
        fsm.act("READ",
                samp_comp.eq(1),
                NextState("WAIT"))

        if has_completion:
            fsm.act("WAIT",
                    self.completion.stb.eq(1),
                    If(self.completion.ack, NextState("IDLE")))
        else:
            fsm.act("WAIT", NextState("IDLE"))

        self.submodules += fsm


