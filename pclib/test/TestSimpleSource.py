#=======================================================================
# TestSimpleSource
#=======================================================================

from pymtl      import *
from pclib.ifcs import OutValRdyBundle

#-----------------------------------------------------------------------
# TestSimpleSource
#-----------------------------------------------------------------------
class TestSimpleSource( Model ):
  'Outputs data provided in ``msgs`` onto a val/rdy interface.'

  def __init__( s, dtype, msgs ):

    s.out  = OutValRdyBundle( dtype )
    s.done = OutPort        ( 1     )

    s.msgs = msgs
    s.idx  = 0

    @s.tick
    def tick():

      # Handle reset

      if s.reset:
        if s.msgs:
          s.out.msg.next = s.msgs[0]
        s.out.val  .next = False
        s.done     .next = False
        return

      # Check if we have more messages to send.

      if ( s.idx == len(s.msgs) ):
        if s.msgs:
          s.out.msg.next = s.msgs[0]
        s.out.val  .next = False
        s.done     .next = True
        return

      # At the end of the cycle, we AND together the val/rdy bits to
      # determine if the output message transaction occured

      out_go = s.out.val and s.out.rdy

      # If the output transaction occured, then increment the index.

      if out_go:
        s.idx = s.idx + 1

      # The output message is always the indexed message in the list, or if
      # we are done then it is the first message again.

      if ( s.idx < len(s.msgs) ):
        s.out.msg.next = s.msgs[s.idx]
        s.out.val.next = True
        s.done   .next = False
      else:
        s.out.msg.next = s.msgs[0]
        s.out.val.next = False
        s.done   .next = True

  def line_trace( s ):

    return "({:2}) {}".format( s.idx, s.out )

