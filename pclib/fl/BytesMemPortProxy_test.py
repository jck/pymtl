#=========================================================================
# BytesMemPortProxy_test
#=========================================================================

from __future__ import print_function

import pytest

from pymtl      import *
from pclib.ifcs import *
from pclib.test import *

from Bytes             import Bytes
from BytesMemPortProxy import BytesMemPortProxy

#-------------------------------------------------------------------------
# Function Implementation
#-------------------------------------------------------------------------
# This is a plain function implementation which copies n bytes in memory.

def mem_copy( mem, src_ptr, dest_ptr, nbytes ):

  for i in range(nbytes):
    mem[dest_ptr+i] = mem[src_ptr+i]

#-------------------------------------------------------------------------
# Test for underlying mem_copy
#-------------------------------------------------------------------------

def test_mem_copy():

  data = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17 ]
  data_bytes = Bytes(18)
  for i in range(18):
    data_bytes[i] = data[i]

  mem_copy( data_bytes, 4, 12, 4 )

  data_ref = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 4, 5, 6, 7, 16, 17 ]
  data_ref_bytes = Bytes(18)
  for i in range(18):
    data_ref_bytes[i] = data_ref[i]

  assert data_bytes == data_ref_bytes

#-------------------------------------------------------------------------
# MemCopy
#-------------------------------------------------------------------------
# An example model that simply copies n bytes from a source pointer to a
# destination pointer in a memory.

class MemCopy (Model):

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( s, memreq_params, memresp_params,
                src_ptr, dest_ptr, nbytes ):

    s.src_ptr  = src_ptr
    s.dest_ptr = dest_ptr
    s.nbytes   = nbytes
    s.done     = False

    # Short names

    mreq_p  = memreq_params
    mresp_p = memresp_params

    # Memory request/response ports

    s.memreq  = InValRdyBundle  ( mreq_p.nbits  )
    s.memresp = OutValRdyBundle ( mresp_p.nbits )

    # BytesMemPortProxy object

    s.mem = BytesMemPortProxy( mreq_p, mresp_p, s.memreq, s.memresp )

    # This looks like a regular tick block, but because it is a
    # pausable_tick there is something more sophisticated is going on.
    # The first time we call the tick, the mem_copy function will try to
    # ready from memory. This will get proxied to the BytesMemPortProxy
    # which will create a memory request and send it out the memreq port.
    # Since we do not have the data yet, we cannot return the data to the
    # mem_copy function so instead we use greenlets to switch back to the
    # pausable tick function. The next time we call tick we jump back
    # into the BytesMemPortProxy object to see if the response has
    # returned. When the response eventually returns, the
    # BytesMemPortProxy object will return the data and the underlying
    # mem_copy function will move onto writing the memory.

    @s.tick_fl
    def logic():
      mem_copy( s.mem, s.src_ptr, s.dest_ptr, s.nbytes )
      s.done = True

  #-----------------------------------------------------------------------
  # done
  #-----------------------------------------------------------------------

  def done( s ):
    return s.done

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return "(" + s.mem.line_trace() + ")"

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------
class TestHarness( Model ):

  def __init__( s, mem_delay, src_ptr, dest_ptr, nbytes ):

    # Create parameters

    memreq_params  = mem_msgs.MemReqParams( 32, 32 )
    memresp_params = mem_msgs.MemRespParams( 32 )

    # Instantiate models

    s.mcopy = MemCopy( memreq_params, memresp_params,
                       src_ptr, dest_ptr, nbytes )

    s.mem = TestMemory( memreq_params, memresp_params, 1, mem_delay )

    s.connect( s.mcopy.memreq,  s.mem.reqs[0]  )
    s.connect( s.mcopy.memresp, s.mem.resps[0] )

  def done( s ):
    return s.mcopy.done

  def line_trace( s ):
    return s.mcopy.line_trace() + " " + s.mem.line_trace()

#-------------------------------------------------------------------------
# test
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "mem_delay", [
   0,
   2,
   5,
  10,
])
def test( dump_vcd, mem_delay ):

  # Instantiate and elaborate the model

  model = TestHarness( mem_delay, 0x0004, 0x000c, 4 )
  model.vcd_file = dump_vcd
  model.elaborate()

  # Write test data into the test memory

  for i in range(18):
    model.mem.mem.mem[ 0x0000 + i ] = i

  # Create a simulator using the simulation tool

  sim = SimulationTool( model )

  # Run the simulation

  print()

  sim.reset()
  while not model.done():
    sim.print_line_trace()
    sim.cycle()

  # Add a couple extra ticks so that the VCD dump is nicer

  sim.cycle()
  sim.cycle()
  sim.cycle()

  # Verify the output

  data_ref = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 4, 5, 6, 7, 16, 17 ]
  for i in range(18):
    assert model.mem.mem.mem[ 0x0000 + i ] == data_ref[i]

